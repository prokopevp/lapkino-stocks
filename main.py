from aiogram import executor
import datetime
import logging
import shutil

from aiogram import Bot, Dispatcher
from aiogram import executor
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from constants import GOOGLE
from constants import STOCKS_FILES_LIBRARY
from constants import TELEGRAM_BOT
from db import check_user, create_user, start_db
from schemas import Provider
from services.google import StocksGoogleSheet
from services.mail import Mail
from services.utils import num_to_char

google_sheet = StocksGoogleSheet()
mail = Mail()


logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT.API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

main_menu_markup = InlineKeyboardMarkup(row_width=2) \
    .row(
        InlineKeyboardButton(text='обновить остатки', callback_data='update_stocks'),
        InlineKeyboardButton(text='создать лист настройки', callback_data='init_remote_from_local_answer')
    )

init_local_from_remote_answer = InlineKeyboardMarkup(row_width=2) \
    .row(
        InlineKeyboardButton(text='уверен', callback_data='init_remote_from_local'),
        InlineKeyboardButton(text='нет!', callback_data='to_main_menu')
    )

class User(StatesGroup):
    password = State()


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    if not check_user(message.from_id):
        await message.answer("Пароль!")
        await User.password.set()
    else:
        await message.answer("*Что вы хотите?*", reply_markup=main_menu_markup, parse_mode='markdown')


@dp.callback_query_handler(lambda call: call.data == 'to_main_menu')
async def user_state_entrypoint(callback: types.CallbackQuery):
    if not check_user(callback.message.chat.id):
        await bot.send_message(callback.message.chat.id, "Пароль!")
        await User.password.set()
    else:
        await bot.send_message(callback.message.chat.id, "*Что вы хотите?*", reply_markup=main_menu_markup, parse_mode='markdown')

@dp.message_handler(state=User.password)
async def user_state_password(message: types.Message, state: FSMContext):
    state.finish()

    text = message.text
    
    if not check_user(message.from_id):
        if text == TELEGRAM_BOT.PASSWORD:
            create_user(message.from_id)
            await message.answer("Привет! Что вы хотите?", reply_markup=main_menu_markup)
        else:
            await message.answer("Пароль!")
            await User.password.set()
    
    
@dp.callback_query_handler(lambda call: call.data == 'update_stocks')
async def user_state_entrypoint(callback: types.CallbackQuery):
    from_id = callback.message.chat.id

    if not check_user(from_id):
        await bot.send_message(from_id, "Пароль!")
        await User.password.set()

        return

    await bot.send_message(from_id, "*Начинаю обновлять остатки...*\n_Когда обновление закончится, вам придет сообщение с результатом._\n\nНе стоит здесь пока ничего нажимать!", parse_mode='markdown')
    
    buh_trouble = False
    try:
        google_sheet.update_buh_stocks()
    except Exception as e:
        print(repr(e))
        buh_trouble = True 

    try:
        google_sheet.config.init_local_from_remote()
    except ValueError as e:
        print(repr(e))
        error_fields = ', '.join(map(lambda error: error['loc'][0], e.errors()))

        await bot.send_message(
            from_id, 
            f"*Неправильно заполнен лист настройки!*\n*Ошибочное поле:* {error_fields}\n\n_Обновление приостановлено..._",
            reply_markup=main_menu_markup,
            parse_mode='markdown'
        )
        return 
    except Exception as e:
        print(repr(str(e)))
        await bot.send_message(
            from_id, 
            f"Неправильно заполнен лист настройки! \n_Обновление приостановлено..._",
            reply_markup=main_menu_markup,
            parse_mode='markdown'
        )
        return
        

    uids = mail.get_mail_uids_since(google_sheet.config.global_settings.search_range)
    init_datetime = datetime.datetime.now()
    
    init_providers: list[Provider] = []
    excluded_providers: list[Provider] = []
    wrong_validation_data_providers: list[Provider] = []

    # filter for excluded providers 
    for provider in google_sheet.config.providers:
        if provider.exclude:
            provider.status = "ИСКЛЮЧЕН"
            excluded_providers.append(provider)
        else:
            if provider.is_validations:
                 # getting previous articles for provider 
                current_worksheet_name = provider.provider + f" {provider.current_date.strftime('%d.%m')}" if provider.current_date else provider.provider
                previous_articles = google_sheet.get_col_values(current_worksheet_name, provider.article_col_num_in_google)

                if previous_articles:
                    provider.previous_articles = previous_articles
                else:
                    provider.status = "НЕТ АРТИКУЛОВ ДЛЯ ПРОВЕРКИ"
                    wrong_validation_data_providers.append(provider)
                    continue
            
            init_providers.append(provider)


    providers_with_status = [*excluded_providers]

    while uids and init_providers:
        uid = uids.pop(0)
        
        provider = mail.fetch_message_and_check_validity_for_providers(uid, init_providers, init_datetime)

        if provider:
            providers_with_status.append(provider)
            init_providers.remove(provider)

    try:
        shutil.rmtree(STOCKS_FILES_LIBRARY)
    except FileNotFoundError:
        pass


    # setting status for not found providers
    for not_found_provider in init_providers:
        not_found_provider.status = "НЕ НАЙДЕН"
        providers_with_status.append(not_found_provider)


    # setting datetime to found providers to ignore them on next stocks updates
    for provider in providers_with_status:
        provider.ignore_before = init_datetime

    providers_with_status += wrong_validation_data_providers

    google_sheet.config.update_remote_from_local(providers_with_status)

    all_providers = [*providers_with_status, *excluded_providers]

    # updating stocks data only for found providers
    for provider in filter(lambda provider: provider.status == 'НАЙДЕН', all_providers):
        new_worksheet_name = provider.provider + f" {provider.current_date.strftime('%d.%m')}"

        if provider.previous_date:
            old_worksheet_name = provider.provider + f" {provider.previous_date.strftime('%d.%m')}" 
            google_sheet.set_worksheet(old_worksheet_name)
            google_sheet.worksheet.update_title(new_worksheet_name)
        else:
            google_sheet.set_worksheet(provider.provider)
            google_sheet.worksheet.update_title(new_worksheet_name)

        article_col_char = num_to_char(provider.article_col_num_in_google)
        stocks_col_char = num_to_char(provider.balance_col_num_in_google)

        google_sheet.worksheet.batch_clear([f"{article_col_char}:{article_col_char}", f"{stocks_col_char}:{stocks_col_char}"])

        google_sheet.worksheet.update(
            f"{article_col_char}1:{article_col_char}{len(provider.articles)}", 
            list(zip(provider.articles)), 
            raw=not provider.actions_with_articles_values
        )

        google_sheet.worksheet.update(
            f"{stocks_col_char}1:{stocks_col_char}{len(provider.stocks)}", 
            list(zip(provider.stocks)), 
            raw=not provider.actions_with_balance_values
        )

    found_providers = list(map(lambda p: p.provider, filter(lambda provider: provider.status == 'НАЙДЕН', providers_with_status)))
    ignored_by_date_providers = list(map(lambda p: p.provider, filter(lambda provider: provider.status == 'В ПРЕДЕЛАХ ДАТЫ НЕ НАЙДЕН', providers_with_status)))
    validation_error_providers = list(map(lambda p: p.provider, filter(lambda provider: provider.status == 'НЕ ПРОШЕЛ ВАЛИДАЦИЮ', providers_with_status)))
    wrong_validation_data_providers_str = list(map(lambda p: p.provider, wrong_validation_data_providers))

    result_message = "*Конец!* _Откройте гугл таблицу_"
    result_message += f"\n\n*Найденные поставщики*: {', '.join(found_providers)}" if found_providers else ""
    result_message += f"\n*Не удалось найти:* {', '.join(list(map(lambda p: p.provider, init_providers)))}" if init_providers else ""
    result_message += f"\n*Проигнорированы*: {', '.join(list(map(lambda p: p.provider, excluded_providers)))}" if excluded_providers else ""
    result_message += f'\n*Новых по сравнению с прошлой проверкой не нашлось:* {", ".join(ignored_by_date_providers)}' if ignored_by_date_providers else ""
    result_message += f'\n*Не прошли валидацию:* {", ".join(validation_error_providers)}' if validation_error_providers else ""
    
    result_message += f'\n\n*Нет артикулов в Google Таблице для проверки*: {", ".join(wrong_validation_data_providers_str)}' if wrong_validation_data_providers else ''

    result_message += f"\n\n*Из онлайн таблиц*: Бух" if not buh_trouble else "\n\n*Не удалось обновить Бух!*"

    result_message +=  "\n\n*Что вы хотите?*"

    await bot.send_message(from_id, result_message, parse_mode='markdown', reply_markup=main_menu_markup)


@dp.callback_query_handler(lambda call: call.data == 'init_remote_from_local_answer')
async def user_state_entrypoint(callback: types.CallbackQuery):
    from_id = callback.message.chat.id

    if not check_user(from_id):
        await bot.send_message(from_id, "Пароль!")
        await User.password.set()

        return

    await bot.send_message(
        from_id, 
        "Если в Google таблице уже есть лист настройки, то он будет полностью стерт перед созданием нового.\n\n***Вы уверены?***", 
        parse_mode="markdown",
        reply_markup=init_local_from_remote_answer,
    )


@dp.callback_query_handler(lambda call: call.data == 'init_remote_from_local')
async def user_state_entrypoint(callback: types.CallbackQuery):
    from_id = callback.message.chat.id

    if not check_user(from_id):
        await bot.send_message(from_id, "Пароль!")
        await User.password.set()

        return

    await bot.send_message(from_id, "*Создаю новый лист настройки...*\n_Когда создание закончится, вам придет сюда сообщение с результатом._", parse_mode='markdown')
    
    google_sheet.config.init_remote_from_local()

    result_message = f'*Готово!* _Откройте гугл таблицу и заполните лист "{GOOGLE.CONFIG_WORKSHEET_TITLE}"_'
    result_message +=  "\n\n*Что вы хотите?*"

    await bot.send_message(from_id, result_message, parse_mode='markdown', reply_markup=main_menu_markup)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=start_db())
