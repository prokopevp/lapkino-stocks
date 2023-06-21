import os
from dotenv import load_dotenv

load_dotenv()

class GOOGLE:
    API_JSON_FILENAME = os.environ.get('GOOGLE_API_JSON_FILENAME')
    SHEET_KEY = os.environ.get('GOOGLE_SHEET_KEY')
    CONFIG_WORKSHEET_TITLE = 'Настройка'
    CONFIG_HEADERS = {
        'provider': 'Поставщик', 
        'found': 'Найден', 
        'exclude': 'Исключить', 
        'article_col_num': 'Артикул (номер столбца)', 
        'balance_col_num': 'Остаток (номер столбца)', 
        'name_col_num': 'Наименование (номер столбца)', 
        'worksheet_num': 'Лист', 
        'emails': 'Почты через запятую', 
        'ignore_before': 'Игнорировать до', 
        'is_validations': 'Валидации', 
        'actions_with_balance_values': 'Действия с остатками', 
        'actions_with_articles_values': 'Действия с артикулами',
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