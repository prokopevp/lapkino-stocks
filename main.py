import datetime
from services.google import StocksGoogleSheet
from services.mail import Mail


google_sheet = StocksGoogleSheet()
mail = Mail()

google_sheet.config.init_local_from_remote()

uids = mail.get_mail_uids_since(google_sheet.config.global_settings.search_range)
init_datetime = datetime.datetime.now()

init_providers = []
excluded_providers = []
for provider in google_sheet.config.providers:
    if provider.exclude:
        excluded_providers.append(provider)
    else:
        init_providers.append(provider)
        
providers_with_status = []

while uids and init_providers:
    uid = uids.pop(0)
    
    provider = mail.fetch_message_and_check_validity_for_providers(uid, init_providers, init_datetime)

    if provider:
        providers_with_status.append(provider)
        init_providers.remove(provider)

for not_found_provider in init_providers:
    not_found_provider.status = "НЕ НАЙДЕН"
    providers_with_status.append(provider)

for provider in providers_with_status:
    provider.ignore_before = init_datetime

all_providers = [*providers_with_status, *excluded_providers]


for provider in all_providers:
    google_sheet.set_worksheet(provider.provider)
    google_sheet.worksheet.clear()
    rows_num = max(len(provider.articles), len(provider.stocks), len(provider.names))
    google_sheet.worksheet.update(f"A1:C{rows_num}", list(zip(provider.articles, provider.stocks, provider.names)))


print(f"success: {list(map(lambda p: p.provider, all_providers))}, not found: {list(map(lambda p: p.provider, init_providers))}, excluded: {list(map(lambda p: p.provider, excluded_providers))}, ")
