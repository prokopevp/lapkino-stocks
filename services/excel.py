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
            # elif book_path.endswith('.xlsx'):
            #     self.file_format = 'xlsx'

            #     self.book = openpyxl.load_workbook(book_path)

            #     self.worksheet = self.book.worksheets[worksheet_number]
            


    def clean_cell(self, cell):
        if self.file_format == 'xls':
            return cell.value if cell.ctype not in [self.CTYPES['empty'], self.CTYPES['error']] else ''
        elif self.file_format == 'xlsx':
            return cell
    
    def format_cell(self, value, type = str, zero_on_blank_int: bool = False):
        if not type: return value

        try:
            return type(value)
        except:
            return '' if not zero_on_blank_int else 0
            
    def get_clean_col(self, column_index: int, format_to = str, zero_on_blank_int: bool = False) -> list:
        if self.file_format == 'xls':
            return list(
                map(
                    lambda cell: 
                        self.format_cell(self.clean_cell(cell), format_to, zero_on_blank_int),
                    self.worksheet.col(column_index)
                )
            )[:100]
    
    def get_article_balance_description_cols(
        self,
        article_col_index: int,
        balance_col_index: int,
        description_col_index: int = None,
        articles_cels_format_type: str = None,
    ) -> list[list]:
        print(article_col_index, balance_col_index, description_col_index)

        return [
            self.get_clean_col(article_col_index - 1, format_to=articles_cels_format_type),
            self.get_clean_col(balance_col_index - 1, format_to=int, zero_on_blank_int=True),
            self.get_clean_col(description_col_index - 1),
        ]
    

