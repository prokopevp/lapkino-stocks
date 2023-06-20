import datetime
import os
import gspread
from pydantic import BaseModel, validator

from constants import GOOGLE
from services.utils import num_to_char


class Provider(BaseModel):
    provider: str 
    found: bool
    exclude: bool 
    article_col_num: int 
    balance_col_num: int
    name_col_num: int | None = None
    provider_emails: list[str]
    ignore_before: datetime.datetime | None = None
    worksheet_num: int
    is_validations: bool
    actions_with_balance_values: list
    actions_with_articles_values: list

    @validator('ignore_before', pre=True)
    def none_if_not_provided(cls, value):
        return None if not value else value

    @validator('found', 'exclude', 'is_validations', pre=True)
    def convert_FALSE_and_TRUE_to_bool(cls, value):
        match value:
            case 'FALSE' | '':
                return False
            case 'TRUE':
                return True
            case _:
                return value

    @validator('article_col_num', 'balance_col_num', 'name_col_num', 'worksheet_num', pre=True)
    def convert_to_int(cls, value):
        return int(value)

    @validator('provider_emails', 'actions_with_balance_values', 'actions_with_articles_values', pre=True)
    def convert_str_to_list(cls, value: str):
        if not value:
            return []
        
        return value.replace(' ', '').split(',')
    
    @validator('provider_emails')
    def requiered(cls, value):
        if not value:
            raise ValueError('не указаны почты поставщиков!')
        return value

class Config:
    def __init__(self, outer_self):
        self.outer_self = outer_self

    def init_local_from_remote(self, config_sheet_title = GOOGLE.CONFIG_WORKSHEET_TITLE):
        self.config_sheet = self.outer_self.spreadsheet.worksheet(config_sheet_title)
        all_config_values = self.config_sheet.get_all_values()
        config_headers_full_row = all_config_values[0]

        not_found_headers = set(GOOGLE.CONFIG_HEADERS.values()) - set(config_headers_full_row)
        if not_found_headers:
            raise ValueError(list(not_found_headers))
        
        self.param_column_number = dict(
            (param_name, config_headers_full_row.index(param_human_name)) 
            for param_name, param_human_name in GOOGLE.CONFIG_HEADERS.items()
        )

        providers = filter(lambda provider_row: bool(provider_row[self.param_column_number['provider']]), all_config_values[1:])

        self.providers = list(map(
            lambda provider: 
                Provider(**dict(list(
                    (param_key, provider[param_sheet_index]) 
                    for param_key, param_sheet_index 
                    in self.param_column_number.items()
                ))), 
            providers
        ))

    def init_remote_from_local(self, row_len: int = 26):
        try:
            self.config_sheet = self.outer_self.add_worksheet(title=GOOGLE.CONFIG_WORKSHEET_TITLE)
        except gspread.exceptions.APIError:
            if not hasattr(self, 'config_sheet'):
                self.config_sheet = self.outer_self.spreadsheet.worksheet(GOOGLE.CONFIG_WORKSHEET_TITLE)
        self.config_sheet.clear()
        self.config_sheet.update(f'A1:{num_to_char(len(GOOGLE.CONFIG_HEADERS))}1', [list(GOOGLE.CONFIG_HEADERS.values())])
        


class StocksGoogleSheet():
    def __init__(self):
        full_path = os.path.join(os.path.dirname(os.path.realpath('__file__')), GOOGLE.API_JSON_FILENAME)
        self.config = Config(self)
        self.worker = gspread.service_account(filename=full_path)
        self.spreadsheet = self.worker.open_by_key(GOOGLE.SHEET_KEY)
        self.worksheets_list = self.spreadsheet.worksheets()

    def add_worksheet(self, title: str, rows_num: int = 1000, cols_num: int = 26):
        new_worksheet = self.spreadsheet.add_worksheet(title=title, rows=rows_num, cols=cols_num)
        return new_worksheet


    def set_worksheet(self, title: str, rows_num: int = 1000, cols_num: int = 26):
        try:
            self.worksheet = self.spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            new_worksheet = self.add_worksheet(title=title, rows=rows_num, cols=cols_num)
            self.worksheet = new_worksheet

    def get_cell_value(self, row: int, col: int):
        return self.worksheet.cell(row, col).value

    def get_all_values(self) -> list:
        return self.worksheet.get_all_values()