import re
import nltk


def get_special_characters(text: str) -> str:
    pattern = r'[a-zA-z0-9.,!?/:;\"\'\s]'
    return re.sub(pattern, '', text)


def clean_text(text: str) -> str:
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub('–*', '', text)
    text = re.sub('—', '', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub('←→', '', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(' ', ' ', text)
    return text


def sent_tokenize(text: str) -> list[str]:
    return nltk.sent_tokenize(clean_text(text))


def word_tokenize(text: str) -> list[str]:
    pass
