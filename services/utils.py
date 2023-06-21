def num_to_char(num: int):
    return chr(64 + num)

def char_to_num(char: str):
    return ord(char) - 64

def equal_to_mail_provider(message_from: str, providers: list):
    for provider in providers:
        if message_from in provider.emails:
            return provider
    return None