import base64
import datetime
import email
from email.header import decode_header
import imaplib
import os
from imapclient import imap_utf7
from constants import ALLOWBLE_VALIDATION_POWDER, MAIL_RU, STOCKS_FILES_LIBRARY
from schemas import Provider
from services.decode import get_decoded_string

from services.excel import Excel
from services.utils import char_to_num, equal_to_mail_provider, set_value_in_action
from dateutil import parser


class Mail():
    def __init__(self):
        mail = imaplib.IMAP4_SSL('imap.mail.ru')
        mail.login(MAIL_RU.BOX, MAIL_RU.API_KEY)

        self.mail = mail

    def get_mail_uids_since(self, days: int):
        stocks_folder_name = get_decoded_string(MAIL_RU.FOLDER)

        self.mail.select(f'INBOX/{stocks_folder_name}')

        date = (datetime.date.today() - datetime.timedelta(days)).strftime("%d-%b-%Y")

        result, data = self.mail.uid('search', None, f'(SENTSINCE {date})')
 
        ids_string = data[0]
        
        return ids_string.split()[::-1]


    def fetch_message_and_check_validity_for_providers(self, 
            uid, 
            providers_list: list[Provider], 
            init_datetime: datetime.datetime
        ) -> Provider | None:

        result, data = self.mail.uid('fetch', uid, "(RFC822)")
        encoded_raw_email = data[0][1]
        
        try:
            raw_email = encoded_raw_email.decode('utf-8')
        except UnicodeDecodeError:
            raw_email = encoded_raw_email.decode('latin-1')
        

        email_message = email.message_from_string(raw_email)
        message_from = email.utils.parseaddr(email_message['From'])[1]
        message_date = email.utils.parsedate_to_datetime(email_message['date']).replace(tzinfo=None)

        provider: Provider | None = equal_to_mail_provider(message_from, providers_list)

        if provider and provider.ignore_before and provider.ignore_before > message_date:
            provider.status = "В ПРЕДЕЛАХ ДАТЫ НЕ НАЙДЕН"
            return provider

        if provider and email_message.is_multipart():
            for payload in email_message.walk():
                if payload.get_content_disposition() == 'attachment':
                    path = STOCKS_FILES_LIBRARY
                    if not os.path.exists(path):
                        os.makedirs(path)

                    file_name = decode_header(payload.get_filename())[0][0]
                    if isinstance(file_name, bytes):
                        try:
                            file_name = file_name.decode()
                        except UnicodeDecodeError:
                            file_name = file_name.decode('latin-1')

                    if any(ext in file_name for ext in ['.xls', '.xlsx']):
                        print(f"*найден:* {provider.provider} \n*отправитель*: {message_from} \n*дата письма*: {message_date}")

                        with open(path+file_name, 'wb') as new_file:
                            new_file.write(payload.get_payload(decode=True))

                        e = Excel(path+file_name)
                        stocks_data = e.get_article_and_balance_cols(
                            article_col_index=provider.article_col_num, 
                            balance_col_index=provider.balance_col_num,
                            articles_cels_format_type=str,
                        )

                        if provider.is_validations:
                            new_articles: set = set(stocks_data['articles'])
                            previous_articles: set = set(provider.previous_articles)

                            len_to_calculate_match_powder = len(previous_articles) | 1
                            current_match_powder = len(new_articles & previous_articles) / len_to_calculate_match_powder

                            if current_match_powder < ALLOWBLE_VALIDATION_POWDER:
                                provider.status = "НЕ ПРОШЕЛ ВАЛИДАЦИЮ"
                                
                                return provider

                        for key in stocks_data:
                            setattr(provider, key, stocks_data[key])

                        provider.articles = list(map(
                            lambda article: set_value_in_action(provider.actions_with_articles_values, article), 
                            provider.articles
                        ))

                        provider.stocks = list(map(
                            lambda stock: set_value_in_action(provider.actions_with_balance_values, stock), 
                            provider.stocks
                        ))

                        provider.status = "НАЙДЕН"
                        provider.previous_date = provider.current_date
                        provider.current_date = message_date
                        return provider

        return None
