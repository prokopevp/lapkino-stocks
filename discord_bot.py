import datetime
import shutil

from constants import STOCKS_FILES_LIBRARY, DISCORD_BOT_API
from schemas import Provider
from services.google import StocksGoogleSheet
from services.mail import Mail
from services.utils import num_to_char

google_sheet = StocksGoogleSheet()
mail = Mail()

import discord # Подключаем библиотеку
from discord.ext import commands

intents = discord.Intents.default() # Подключаем "Разрешения"
intents.message_content = True
# Задаём префикс и интенты
bot = commands.Bot(command_prefix='>', intents=intents)

# С помощью декоратора создаём первую команду
@bot.command()
async def stocks(ctx: commands.context.Context):
    await ctx.send("*Начинаю обновлять остатки...*\n\nКогда обновление закончится, вам придет сообщение с результатом.\n**Повторно отправлять команду только если прошло больше 10 минут!**")

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

        await ctx.send(f"*Неправильно заполнен лист настройки!*\n*Ошибочное поле:* {error_fields}\n\n_Обновление приостановлено..._")
        return
    except Exception as e:
        print(repr(str(e)))
        await ctx.send(f"Неправильно заполнен лист настройки! \n_Обновление приостановлено..._")
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
                previous_articles = google_sheet.get_col_values(current_worksheet_name,
                                                                provider.article_col_num_in_google)

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

        google_sheet.worksheet.batch_clear(
            [f"{article_col_char}:{article_col_char}", f"{stocks_col_char}:{stocks_col_char}"])

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

    found_providers = list(
        map(lambda p: p.provider, filter(lambda provider: provider.status == 'НАЙДЕН', providers_with_status)))
    ignored_by_date_providers = list(map(lambda p: p.provider,
                                         filter(lambda provider: provider.status == 'В ПРЕДЕЛАХ ДАТЫ НЕ НАЙДЕН',
                                                providers_with_status)))
    validation_error_providers = list(map(lambda p: p.provider,
                                          filter(lambda provider: provider.status == 'НЕ ПРОШЕЛ ВАЛИДАЦИЮ',
                                                 providers_with_status)))
    wrong_validation_data_providers_str = list(map(lambda p: p.provider, wrong_validation_data_providers))

    result_message = "|\n'-->**Конец!** Откройте гугл таблицу\n"
    result_message += f"\n**Найденные поставщики**: {', '.join(found_providers)}" if found_providers else ""
    result_message += f"\n**Не удалось найти:** {', '.join(list(map(lambda p: p.provider, init_providers)))}" if init_providers else ""
    result_message += f"\n**Проигнорированы**: {', '.join(list(map(lambda p: p.provider, excluded_providers)))}" if excluded_providers else ""
    result_message += f'\n**Новых по сравнению с прошлой проверкой не нашлось:** {", ".join(ignored_by_date_providers)}' if ignored_by_date_providers else ""
    result_message += f'\n**Не прошли валидацию:** {", ".join(validation_error_providers)}' if validation_error_providers else ""

    result_message += f'\n\n*Нет артикулов в Google Таблице для проверки*: {", ".join(wrong_validation_data_providers_str)}' if wrong_validation_data_providers else ''

    result_message += f"\n\n**Из онлайн таблиц**: Бух" if not buh_trouble else "\n\n*Не удалось обновить Бух!*"

    result_message += "\n\n*Чтобы снова обновить остатки напишите `>stocks`*"

    await ctx.send(result_message)


bot.run(DISCORD_BOT_API)