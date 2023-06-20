from services.google import StocksGoogleSheet


google_sheet = StocksGoogleSheet()

google_sheet.config.init_local_from_remote()

print(google_sheet.config.global_settings)