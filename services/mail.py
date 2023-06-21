import base64
import datetime
import email
from email.header import decode_header
import imaplib
import os
from imapclient import imap_utf7
from constants import MAIL_RU
from schemas import Provider
from services.decode import get_decoded_string

from services.excel import Excel
from services.utils import char_to_num, equal_to_mail_provider


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


    def fetch_message_and_print_if_provider(self, uid, providers_list: list[Provider]):
        result, data = self.mail.uid('fetch', uid, "(RFC822)")
        encoded_raw_email = data[0][1]
        
        try:
            raw_email = encoded_raw_email.decode('utf-8')
        except UnicodeDecodeError:
            raw_email = encoded_raw_email.decode('latin-1')
        

        email_message = email.message_from_string(raw_email)
        message_from = email.utils.parseaddr(email_message['From'])[1]

        path = './stocks_files/' 
        if not os.path.exists(path):
            os.makedirs(path)

        provider = equal_to_mail_provider(message_from, providers_list)

        if provider and email_message.is_multipart():
            for payload in email_message.walk():
                if payload.get_content_disposition() == 'attachment':
                    file_name = decode_header(payload.get_filename())[0][0]
                    if isinstance(file_name, bytes):
                        try:
                            file_name = file_name.decode()
                        except UnicodeDecodeError:
                            file_name = file_name.decode('latin-1')

                    if any(ext in file_name for ext in ['.xls', '.xlsx']):
                        print(f"from: {email.utils.parseaddr(email_message['From'])[1]}")
                        print('Downloaded filename: ', file_name)

                        with open(path+file_name, 'wb') as new_file:
                            new_file.write(payload.get_payload(decode=True))

                        e = Excel(path+file_name)
                        print(e.get_article_balance_description_cols(
                            article_col_index=provider.article_col_num, 
                            balance_col_index=provider.balance_col_num,
                            description_col_index=provider.name_col_num,
                            articles_cels_format_type=str,
                        ))
                        return provider

        return None
