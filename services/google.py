import os
import gspread

from constants import GOOGLE
from schemas import GlobalSettings, Provider
from services.utils import num_to_char


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

        self.global_settings = GlobalSettings(**dict(list(
            (list(
                setting_key for setting_key in GOOGLE.GLOBAL_SETTINGS 
                if GOOGLE.GLOBAL_SETTINGS[setting_key] == setting_item[0]
            )[0],
            setting_item[1]) 
            for setting_item in list((
                    row[self.param_column_number['global_settings']], 
                    row[self.param_column_number['global_settings_values']]
                ) for row in all_config_values[1:])
            if setting_item[0]
        )))

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

        settings_keys = list(GOOGLE.GLOBAL_SETTINGS)
        global_settings_char_index_in_sheet = num_to_char(list(GOOGLE.CONFIG_HEADERS).index('global_settings') + 1)
        
        if settings_keys:
            self.config_sheet.update(
                f"{global_settings_char_index_in_sheet}2:{global_settings_char_index_in_sheet}{len(settings_keys)+1}", 
                [[GOOGLE.GLOBAL_SETTINGS[key]] for key in settings_keys]
            )
        


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