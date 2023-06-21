from services.excel import Excel
from services.google import StocksGoogleSheet
from services.mail import Mail
from services.utils import char_to_num


google_sheet = StocksGoogleSheet()
mail = Mail()

google_sheet.config.init_local_from_remote()

uids = mail.get_mail_uids_since(google_sheet.config.global_settings.search_range)

while uids and google_sheet.config.providers:
    uid = uids.pop(0)
    
    provider = mail.fetch_message_and_print_if_provider(uid, google_sheet.config.providers)
    if provider:
        google_sheet.config.providers.remove(provider)
