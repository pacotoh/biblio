import os
import json

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import word_tokenize, sent_tokenize
import numpy as np


CONFIG_JSON = 'config/embeddings.json'
config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
INFO_BASE_PATH = config['info_base_path']
LANGUAGE = config['language']


def load_text(filename: str) -> str:
    with open(f'{INFO_BASE_PATH}{filename}/{filename}_text.txt', 'r') as text:
        content = text.read()
    return content


def create_corpus(base_path: str) -> dict[str, str]:
    files = os.listdir(base_path)
    return {file: load_text(f'{file}') for file in files}


def tf_idf(base_path: str) -> TfidfVectorizer:
    tfidf_vec = TfidfVectorizer(stop_words=LANGUAGE)
    corpus = create_corpus(base_path)
    return tfidf_vec.fit_transform(corpus.values())


def co_ocurrence_matrix(corpus: list, window_size: int = 3) -> dict[str, np.array]:
    unique_words = set()
    for text in corpus:
        for word in word_tokenize(text):
            unique_words.add(word)

    word_search_dict = {word: np.zeros(shape=(len(unique_words))) for word in unique_words}
    word_list = list(word_search_dict.keys())
    for text in corpus:
        text_list = word_tokenize(text)
        for idx, word in enumerate(text_list):
            i = max(0, idx - window_size)
            j = min(len(text_list) - 1, idx + window_size)
            search = [text_list[idx_] for idx_ in range(i, j+1)]
            search.remove(word)
            for neighbor in search:
                nei_idx = word_list.index(neighbor)
                word_search_dict[word][nei_idx] += 1
    return word_search_dict


def word_to_vec() -> None:
    pass


def fast_text() -> None:
    pass


def cbow() -> None:
    pass


def skip_gram() -> None:
    pass


def export_data(base_path: str) -> None:
    corpus = create_corpus(base_path)
    for text in corpus.items():
        sentences = sent_tokenize(text[1])
        name = text[0]
        # TODO: Create co-ocurrence matrices concurrently
        com = co_ocurrence_matrix(sentences)
        pd.DataFrame(com, index=com.keys()).astype('int').to_csv(f'{base_path}{name}/{name}_com.csv')


if __name__ == '__main__':
    export_data(INFO_BASE_PATH)
