import os
import json

CONFIG_JSON = 'config/embeddings.json'
config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
INFO_BASE_PATH = config['info_base_path']


def load_text(filename: str) -> str:
    with open(f'{INFO_BASE_PATH}{filename}/{filename}_text.txt', 'r') as text:
        content = text.read()
    return content


def create_corpus() -> list[str]:
    files = os.listdir(f'{INFO_BASE_PATH}/')
    return [load_text(f'{file}') for file in files]


def tf_idf() -> None:
    pass


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
    print(create_corpus())
