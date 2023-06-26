import datetime
from pydantic import BaseModel, Field, validator
from dateutil import parser
from constants import GOOGLE

from services.utils import char_to_num


class Provider(BaseModel):
    provider: str = Field(..., alias=GOOGLE.CONFIG_HEADERS['provider'])
    status: str | None
    exclude: bool = Field(..., alias=GOOGLE.CONFIG_HEADERS['exclude'])
    article_col_num: int = Field(..., alias=GOOGLE.CONFIG_HEADERS['article_col_num'])
    balance_col_num: int = Field(..., alias=GOOGLE.CONFIG_HEADERS['balance_col_num'])
    article_col_num_in_google: int = Field(..., alias=GOOGLE.CONFIG_HEADERS['article_col_num_in_google'])
    balance_col_num_in_google: int = Field(..., alias=GOOGLE.CONFIG_HEADERS['balance_col_num_in_google'])
    emails: list[str] = Field(..., alias=GOOGLE.CONFIG_HEADERS['emails'])
    ignore_before: datetime.datetime | None = Field(None, alias=GOOGLE.CONFIG_HEADERS['ignore_before'])
    worksheet_num: int = Field(..., alias=GOOGLE.CONFIG_HEADERS['worksheet_num'])
    is_validations: bool = Field(..., alias=GOOGLE.CONFIG_HEADERS['is_validations'])
    actions_with_balance_values: str = ''
    actions_with_articles_values: str = ''
    current_date: datetime.datetime | None = Field(None, alias=GOOGLE.CONFIG_HEADERS['current_date'])
    previous_date: datetime.datetime | None = Field(None, alias=GOOGLE.CONFIG_HEADERS['previous_date'])
    articles: list = []
    stocks: list = []

    previous_articles: list = []

    @validator('status', pre=True)
    def none_if_not_provided(cls, value):
        return None if not value else value
    
    @validator('ignore_before', 'current_date', 'previous_date', pre=True)
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

    @validator(
        'article_col_num', 
        'balance_col_num', 
        'article_col_num_in_google', 
        'balance_col_num_in_google', 
        'worksheet_num', 
        pre=True
    )
    def convert_to_int(cls, value):
        try:
            return int(value)
        except:
            return char_to_num(value.upper())

    @validator('emails', pre=True)
    def convert_str_to_list(cls, value: str):
        if not value:
            return []
        
        return value.replace(' ', '').split(',')
    
    @validator('emails')
    def requiered(cls, value):
        if not value:
            raise ValueError('не указаны почты поставщиков!')
        return value
    
    class Config:
        allow_population_by_field_name = True
    

class GlobalSettings(BaseModel):
    search_range: int = Field(..., alias=GOOGLE.GLOBAL_SETTINGS['search_range'])

    @validator('search_range', pre=True)
    def convert_to_int(cls, value):
        return int(value)
    
    class Config:
        allow_population_by_field_name = True