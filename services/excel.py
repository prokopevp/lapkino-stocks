import os
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


    def __init__(self, book_path=''):
        if book_path and os.path.exists(book_path):
            try:
                self.book = xlrd.open_workbook(book_path, formatting_info=True)
            except NotImplementedError:
                self.book = xlrd.open_workbook(book_path)


    def clean_row(self, row: list) -> list:
        return list(
            map(
                lambda cell: cell.value 
                if cell.ctype not in [
                        self.CTYPES['empty'], 
                        self.CTYPES['error']
                    ] 
                    else '', 
                row
            )
        )
    
    def get_all_rows(self, only_values=False, sheet_index=0) -> list:
        sh = self.book.sheet_by_index(sheet_index)

        return list(
            map(
                lambda rx: self.clean_row(sh.row(rx)) if only_values else sh.row(rx), 
                range(sh.nrows)
            )
        )
    
    def format_cell(self, value, type: str = None, zero_on_blank_int: bool = False):
        if not type: return value

        def format_or_blank(value, type):
            try:
                return type(value)
            except:
                return '' if not zero_on_blank_int else 0


        match type:
            case 'int':
                return format_or_blank(value, int)
            case 'str':
                return format_or_blank(value, str)
            case other:
                return value

    
    def get_clean_col(self, 
            index: int, 
            sheet_index: int = 0, 
            format_type: str = None,
            zero_on_blank_int: bool = False,
        ) -> list:
        rows = self.get_all_rows(only_values=True, sheet_index=sheet_index)

        return list(
            map(
                lambda row: self.format_cell(row[index], format_type, zero_on_blank_int),
                rows,
            )
        )
    
    def get_article_balance_description_cols(
        self,
        article_col_index: int,
        balance_col_index: int,
        description_col_index: int = None,
        articles_cels_format_type: str = None,
    ) -> list[list]:
        return [
            self.get_clean_col(article_col_index, format_type=articles_cels_format_type),
            self.get_clean_col(balance_col_index, format_type='int', zero_on_blank_int=True),
            self.get_clean_col(description_col_index),
        ]
    

