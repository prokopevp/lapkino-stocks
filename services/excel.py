import os
import openpyxl
import xlrd

class Excel:
    CTYPES = {
        'empty': 0,
        'text': 1,
        'number': 2,
        'date': 3,
        'bool': 4,
        'error': 5,
        'blank': 6,
    }


    def __init__(self, book_path: str = '', worksheet_number: int = 0):
        if book_path and os.path.exists(book_path):
            # if book_path.endswith('.xls'):
            self.file_format = 'xls'

            try:
                self.book = xlrd.open_workbook(book_path, formatting_info=True)
            except NotImplementedError:
                self.book = xlrd.open_workbook(book_path)

            self.worksheet = self.book.sheet_by_index(worksheet_number)
            


    def clean_cell(self, cell):
        if cell.ctype in [self.CTYPES['empty'], self.CTYPES['error']]:
            return ''
        if cell.ctype == self.CTYPES['number']:
            return str(cell.value).rstrip('0').rstrip('.')
        return cell.value
    
    def format_cell(self, value, type = str, zero_on_blank_int: bool = False):
        if not type: return value

        try:
            return type(value)
        except:
            return '' if not zero_on_blank_int else 0
            
    def get_clean_col(self, column_index: int, format_to = str, zero_on_blank_int: bool = False) -> list:
        return list(
            map(
                lambda cell: 
                    self.format_cell(self.clean_cell(cell), format_to, zero_on_blank_int),
                self.worksheet.col(column_index)
            )
        )
    
    def get_article_balance_description_cols(
        self,
        article_col_index: int,
        balance_col_index: int,
        description_col_index: int = None,
        articles_cels_format_type: str = None,
    ) -> dict[str, list]:
        return {
            "articles": self.get_clean_col(article_col_index - 1, format_to=articles_cels_format_type),
            "stocks": self.get_clean_col(balance_col_index - 1, format_to=int, zero_on_blank_int=True),
            "names": self.get_clean_col(description_col_index - 1),
        }
    

