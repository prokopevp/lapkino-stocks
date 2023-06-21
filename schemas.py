import datetime
from pydantic import BaseModel, validator
from dateutil import parser

from services.utils import char_to_num


class Provider(BaseModel):
    provider: str 
    status: str | None
    exclude: bool 
    article_col_num: int 
    balance_col_num: int
    name_col_num: int | None = None
    emails: list[str]
    ignore_before: datetime.datetime | None = None
    worksheet_num: int
    is_validations: bool
    actions_with_balance_values: list
    actions_with_articles_values: list

    articles: list = []
    stocks: list = []
    names: list = []

    @validator('ignore_before', 'status', pre=True)
    def none_if_not_provided(cls, value):
        
        return None if not value else value
    
    @validator('ignore_before', pre=True)
    def convert_to_date(cls, value):
        return None if not value else parser.parse(value)   

    @validator('exclude', 'is_validations', pre=True)
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
        try:
            return int(value)
        except:
            return char_to_num(value.upper())

    @validator('emails', 'actions_with_balance_values', 'actions_with_articles_values', pre=True)
    def convert_str_to_list(cls, value: str):
        if not value:
            return []
        
        return value.replace(' ', '').split(',')
    
    @validator('emails')
    def requiered(cls, value):
        if not value:
            raise ValueError('не указаны почты поставщиков!')
        return value
    

class GlobalSettings(BaseModel):
    search_range: int

    @validator('search_range', pre=True)
    def convert_to_int(cls, value):
        return int(value)