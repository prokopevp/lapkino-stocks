from services.google import StocksGoogleSheet


google_sheet = StocksGoogleSheet()

google_sheet.config.init_remote_from_local()