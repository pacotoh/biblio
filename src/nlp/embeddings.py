import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer


CONFIG_JSON = 'config/embeddings.json'
config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
INFO_BASE_PATH = config['info_base_path']


def load_text(filename: str) -> str:
    with open(f'{INFO_BASE_PATH}{filename}/{filename}_text.txt', 'r') as text:
        content = text.read()
    return content


def create_corpus(base_path: str) -> dict[str, str]:
    files = os.listdir(base_path)
    return {file: load_text(f'{file}') for file in files}


def tf_idf(base_path: str) -> TfidfVectorizer:
    tfidf_vec = TfidfVectorizer(stop_words='english')
    corpus = create_corpus(base_path)
    return tfidf_vec.fit_transform(corpus.values())


def word_to_vec() -> None:
    pass


def fast_text() -> None:
    pass


def co_ocurrence_matrix() -> None:
    pass


def cbow() -> None:
    pass


def skip_gram() -> None:
    pass


if __name__ == '__main__':
    print(tf_idf(INFO_BASE_PATH))
