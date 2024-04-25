import os
import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import word_tokenize, sent_tokenize
import numpy as np
from pyspark.sql import SparkSession
from pyspark import SparkContext, RDD
from pyspark.mllib.feature import HashingTF, IDF

CONFIG_JSON = 'config/embeddings.json'
config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
INFO_BASE_PATH = config['info_base_path']
LANGUAGE = config['language']
HASHING_FEATURES = config['hashing_features']

spark = SparkSession.builder.master('local[*]').appName('spark-tfidf').getOrCreate()
sc = SparkContext.getOrCreate()


def load_text(filename: str) -> str:
    with open(f'{INFO_BASE_PATH}{filename}/{filename}_text.txt', 'r') as text:
        content = text.read()
    return content


def create_corpus(base_path: str) -> dict[str, str]:
    files = os.listdir(base_path)
    return {file: load_text(f'{file}') for file in files}


def tf_idf(corpus_param: dict):
    tfidf_vec = TfidfVectorizer(stop_words=LANGUAGE)
    return tfidf_vec.fit_transform(corpus_param.values())


def co_ocurrence_matrix(corpus_param: list, window_size: int = 3) -> dict[str, np.array]:
    unique_words = set()
    for text in corpus_param:
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


def export_com(base_path: str, corpus_param: dict) -> None:
    for text in corpus_param.items():
        sentences = sent_tokenize(text[1])
        name = text[0]
        # TODO: Create co-ocurrence matrices concurrently
        com = co_ocurrence_matrix(sentences)
        pd.DataFrame(com, index=com.keys()).astype('int').to_csv(f'{base_path}{name}/{name}_com.csv')


def hash_tf_search(data_path: str, word_search: str, min_doc_freq: int = 2) -> RDD[tuple[float, str]]:
    raw_data = sc.textFile(data_path)
    fields = raw_data.map(lambda x: x.split('\t'))
    documents = fields.map(lambda x: x[3].split(' '))
    document_names = fields.map(lambda x: x[1])

    hashing = HashingTF(HASHING_FEATURES)
    tf = hashing.transform(documents)
    idf = IDF(minDocFreq=min_doc_freq).fit(tf)
    tfidf = idf.transform(tf)
    word_tf = hashing.transform([word_search])

    word_hash_value = word_tf.indices[0]
    word_relevance = tfidf.map(lambda x: x[int(word_hash_value)])

    return word_relevance.zip(document_names)


def word_to_vec() -> None:
    pass


def fast_text() -> None:
    pass


def cbow() -> None:
    pass


def skip_gram() -> None:
    pass


if __name__ == '__main__':
    corpus = create_corpus(INFO_BASE_PATH)
    tf_idf(corpus).toarray().tofile(f'{INFO_BASE_PATH}tfidf.csv', sep=',')
    print(tf_idf(corpus))
