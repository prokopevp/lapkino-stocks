import os
import gspread

from constants import GOOGLE
from schemas import GlobalSettings, Provider
from services.utils import char_to_num, num_to_char


class Config:
    def __init__(self, outer_self):
        self.outer_self = outer_self

    def init_local_from_remote(self, config_sheet_title = GOOGLE.CONFIG_WORKSHEET_TITLE):
        self.config_sheet = self.outer_self.spreadsheet.worksheet(config_sheet_title)
        all_config_values = self.config_sheet.get_all_values()
        config_headers_full_row = all_config_values[0]

        not_found_headers = set(GOOGLE.CONFIG_HEADERS.values()) - set(config_headers_full_row)
        if not_found_headers:
            raise ValueError(f'не найдены настройки: {",".join(list(not_found_headers))}')
        
        self.param_column_number = dict(
            (param_name, config_headers_full_row.index(param_human_name)) 
            for param_name, param_human_name in GOOGLE.CONFIG_HEADERS.items()
        )

        first_config_column = self.config_sheet.col_values(1)
        second_config_column = self.config_sheet.col_values(2)
        
        index_of_global_settings_header = first_config_column.index(GOOGLE.GLOBAL_SETTINGS_HEADERS['global_settings'])

        settings_keys = list(
            list(GOOGLE.GLOBAL_SETTINGS.keys())[
                list(GOOGLE.GLOBAL_SETTINGS.values()).index(setting_human_key)
            ] 
            for setting_human_key 
            in first_config_column[index_of_global_settings_header + 1:]
        )

        settings_values = second_config_column[index_of_global_settings_header + 1]

        self.global_settings = GlobalSettings(**dict(zip(settings_keys, settings_values)))

        providers = filter(lambda provider_row: bool(provider_row[self.param_column_number['provider']]), all_config_values[1:index_of_global_settings_header])

        self.providers = list(map(
            lambda provider: 
                Provider(**dict(list(
                    (param_key, provider[param_sheet_index]) 
                    for param_key, param_sheet_index 
                    in self.param_column_number.items()
                ))), 
            providers
        ))

    def update_remote_from_local(self, providers: list[Provider]):
        status_column_char = num_to_char(self.param_column_number['status'] + 1)
        ignore_before_column_char = num_to_char(self.param_column_number['ignore_before'] + 1)
        previous_date_column_char = num_to_char(self.param_column_number['previous_date'] + 1)
        current_date_column_char = num_to_char(self.param_column_number['current_date'] + 1)

        for provider in providers:
            provider_row = self.config_sheet.find(provider.provider).row
            
            self.config_sheet.update(f"{status_column_char}{provider_row}", provider.status)
            self.config_sheet.update(f"{ignore_before_column_char}{provider_row}", str(provider.ignore_before or ''))
            self.config_sheet.update(f"{previous_date_column_char}{provider_row}", str(provider.previous_date or ''))
            self.config_sheet.update(f"{current_date_column_char}{provider_row}", str(provider.current_date or ''))


    def init_remote_from_local(self, row_len: int = 26):
        try:
            self.config_sheet = self.outer_self.add_worksheet(title=GOOGLE.CONFIG_WORKSHEET_TITLE)
        except gspread.exceptions.APIError:
            if not hasattr(self, 'config_sheet'):
                self.config_sheet = self.outer_self.spreadsheet.worksheet(GOOGLE.CONFIG_WORKSHEET_TITLE)
        self.config_sheet.clear()
        self.config_sheet.update(f'A1:{num_to_char(len(GOOGLE.CONFIG_HEADERS))}1', [list(GOOGLE.CONFIG_HEADERS.values())])

        
        self.config_sheet.update(f"A4:B4", [[*GOOGLE.GLOBAL_SETTINGS_HEADERS.values()]])
        if GOOGLE.GLOBAL_SETTINGS:
            global_settings = list(zip(GOOGLE.GLOBAL_SETTINGS.values()))
            print(global_settings)
            self.config_sheet.update(f"A5:A{4+len(GOOGLE.GLOBAL_SETTINGS)}", global_settings)
        


class StocksGoogleSheet():
    def __init__(self):
        full_path = os.path.join(os.path.dirname(os.path.realpath('__file__')), GOOGLE.API_JSON_FILENAME)
        self.config = Config(self)
        self.worker = gspread.service_account(filename=full_path)
        self.spreadsheet = self.worker.open_by_key(GOOGLE.SHEET_KEY)
        self.worksheets_list = self.spreadsheet.worksheets()

    
    def update_buh_stocks(self):
        buh_sheet = self.worker.open_by_key(GOOGLE.BUH_GOOGLE_SHEET_API_KEY)

        buh_worksheet = buh_sheet.worksheet('бух')
        

        buh_articles = buh_worksheet.col_values(char_to_num("D"))
        buh_names = buh_worksheet.col_values(char_to_num("E"))
        buh_stocks = buh_worksheet.col_values(char_to_num("F"))

        num_of_rows = max(
            map(
                lambda col: len(col), 
                [buh_stocks, buh_names, buh_articles]
            )
        )

        try:
            our_buh_worksheet = self.spreadsheet.worksheet('Бух')
        except gspread.exceptions.WorksheetNotFound:
            our_buh_worksheet = self.add_worksheet(title="Бух", rows_num=1000, cols_num=24)

        our_buh_worksheet.update( 
            f"B1:D{num_of_rows}",
            list(zip(buh_articles, buh_names, buh_stocks)),
            raw = True,
        )
        

    def add_worksheet(self, title: str, rows_num: int = 1000, cols_num: int = 26):
        new_worksheet = self.spreadsheet.add_worksheet(title=title, rows=rows_num, cols=cols_num)
        return new_worksheet


    def set_worksheet(self, title: str, rows_num: int = 1000, cols_num: int = 26):
        try:
            self.worksheet = self.spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            new_worksheet = self.add_worksheet(title=title, rows_num=rows_num, cols_num=cols_num)
            self.worksheet = new_worksheet

    def get_cell_value(self, row: int, col: int):
        return self.worksheet.cell(row, col).value

    def get_all_values(self) -> list:
        return self.worksheet.get_all_values()
    
    def get_col_values(self, worksheet_title: str, col_num: int) -> list:
        try:
            provider_worksheet = self.spreadsheet.worksheet(worksheet_title)
            from_provider_google_worksheet_column_values = provider_worksheet.col_values(col_num)
            return from_provider_google_worksheet_column_values
        except gspread.exceptions.WorksheetNotFound:
            return []