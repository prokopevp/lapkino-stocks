import base64
import datetime
import email
from email.header import decode_header
import imaplib
import os
from imapclient import imap_utf7
from constants import MAIL_RU
from services.decode import get_decoded_string

from services.excel import Excel


class Mail():
    def __init__(self):
        mail = imaplib.IMAP4_SSL('imap.mail.ru')
        mail.login(MAIL_RU.BOX, MAIL_RU.API_KEY)

        self.mail = mail

    def print_last_stocks(self):
        stocks_folder_name = f"/{get_decoded_string(MAIL_RU.FOLDER)}" if MAIL_RU.FOLDER else ""

        self.mail.select(f'INBOX/{stocks_folder_name}')

        date = (datetime.date.today() - datetime.timedelta(1)).strftime("%d-%b-%Y")

        result, data = self.mail.uid('search', None, f'(SENTSINCE {date})')
 
        ids_string = data[0]
        ids = ids_string.split()[::-1][:10]
        
        for id in ids:
            result, data = self.mail.uid('fetch', id, "(RFC822)")
            encoded_raw_email = data[0][1]
            
            try:
                raw_email = encoded_raw_email.decode('utf-8')
            except UnicodeDecodeError:
                raw_email = encoded_raw_email.decode('latin-1')
            

            email_message = email.message_from_string(raw_email)

            path = './stocks_files/' 
            if not os.path.exists(path):
                os.makedirs(path)

            print(f"from: {email.utils.parseaddr(email_message['From'])[1]}")

            if email_message.is_multipart():
                for payload in email_message.walk():
                    if payload.get_content_disposition() == 'attachment':
                        print(f"from: {email.utils.parseaddr(email_message['From'])[1]}")
                        print(f"when: {email_message['Date']}")
                        file_name = decode_header(payload.get_filename())[0][0]
                        if isinstance(file_name, bytes):
                            try:
                                file_name = file_name.decode()
                            except UnicodeDecodeError:
                                file_name = file_name.decode('latin-1')
                        print("'--> " + file_name)

                        print('!!!!!!', file_name)
                        if any(ext in file_name for ext in ['.xls', '.xlsx']):
                            print('Downloaded filename: ', file_name)

                            with open(path+file_name, 'wb') as new_file:
                                new_file.write(payload.get_payload(decode=True))

                            excel = Excel(path+file_name)
                            excel.print_all_rows()
