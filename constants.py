import os
from dotenv import load_dotenv

load_dotenv()

class GOOGLE:
    API_JSON_FILENAME = os.environ.get('GOOGLE_API_JSON_FILENAME')
    SHEET_KEY = os.environ.get('GOOGLE_SHEET_KEY')
    CONFIG_WORKSHEET_TITLE = 'Настройка'
    BUH_GOOGLE_SHEET_API_KEY = os.environ.get("BUH_GOOGLE_SHEET_API_KEY")

    CONFIG_HEADERS = {
        'provider': 'Поставщик', 
        'status': 'Статус', 
        'exclude': 'Исключить', 
        'article_col_num': 'Артикул у поставщика (номер столбца)', 
        'balance_col_num': 'Остаток у поставщика (номер столбца)', 
        'article_col_num_in_google': 'Артикул google (номер столбца)', 
        'balance_col_num_in_google': 'Остаток google (номер столбца)', 
        'worksheet_num': 'Лист', 
        'emails': 'Почты через запятую', 
        'current_date': 'Дата актуальных остатков',
        'ignore_before': 'Дата проверки', 
        'previous_date': 'Дата прошлых остатков',
        'is_validations': 'Валидации', 
        'actions_with_balance_values': 'Действия с остатками', 
        'actions_with_articles_values': 'Действия с артикулами',
    }

    GLOBAL_SETTINGS_HEADERS = {
        'global_settings': 'Общие настройки',
        'global_settings_values': 'Значения глобальных настроек',
    }

    GLOBAL_SETTINGS = {
        'search_range': 'За сколько дней проверять',
    }

class MAIL_RU:
    BOX=os.environ.get('MAIL_RU_BOX')
    API_KEY=os.environ.get('MAIL_RU_API_KEY')
    FOLDER=os.environ.get("MAIL_RU_FOLDER")

ALLOWBLE_VALIDATION_POWDER = 0.1
ACTION_PARSE_VALUE = "ЯЧЕЙКА"

STOCKS_FILES_LIBRARY = './stocks_files/' 

class TELEGRAM_BOT:
    API_TOKEN = os.environ.get("TELEGRAM_BOT_API_TOKEN")
    PASSWORD = os.environ.get("TELEGRAM_BOT_PASSWORD")