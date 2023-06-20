from imapclient import imap_utf7


def get_decoded_string(string: str) -> bytes:
    return imap_utf7.encode(string).decode()