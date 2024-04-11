import re
import json
import nltk
import spacy

nlp = spacy.load("en_core_web_sm")


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


def lexical_attributes(text: str) -> dict:
    doc = nlp(text)
    return {token.text: [token.i,
                         token.is_alpha,
                         token.is_punct,
                         token.like_num,
                         token.pos_,
                         token.dep_,
                         token.head.text]
            for token in doc}


def named_entities(text: str) -> dict:
    doc = nlp(text)
    return {ent.text: (ent.label_, spacy.explain(ent.label_)) for ent in doc.ents}

