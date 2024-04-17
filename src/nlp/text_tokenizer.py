import json
import os
import pickle
import re
from dataclasses import dataclass, field
import nltk
import spacy
from spacy.tokens.doc import Doc
import pandas as pd
import logging
from datetime import datetime
import argparse
import concurrent.futures

CONFIG_JSON = 'config/text_tokenizer.json'
LOG_FILE = datetime.now().strftime('%Y%m%d%H%M%S')
config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
nlp = spacy.load(config['spacy_model_en'])
nlp.max_length = config['nlp_max_length']

logging.basicConfig(
    filename=f'../../logs/TT{LOG_FILE}.log',
    level=logging.INFO,
    format='[%(asctime)s]: %(levelname)s %(message)s'
)


@dataclass
class TextProperties:
    path: str = field(init=True)
    text: str = field(default='', init=False)
    sentences: list = field(default_factory=list, init=False)
    tokens: list = field(default_factory=list, init=False)
    entities: dict = field(default_factory=dict, init=False)
    lexical: dict = field(default_factory=dict, init=False)
    special_chars: str = field(init=False)

    def __post_init__(self) -> None:
        with open(self.path, 'r') as file:
            self.text = file.read()

        self.filename = self.path.split('/')[-1]
        logging.info(msg=f'STARTED: TextProperties generation for {self.filename}: {datetime.now()}')
        self._clean_text()
        self.doc = nlp(self.text)
        self.lexical = self._lexical_attributes()
        self.sentences = self._sent_tokenize()
        self.entities = self._named_entities()
        self.special_chars = self._special_characters()
        self.verbs_lemma = set([token.lemma_ for token in self.doc if token.pos_ == "VERB"])
        logging.info(msg=f'FINISHED: TextProperties generation for {self.filename}: {datetime.now()}')

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        del state['doc']
        return state

    def _special_characters(self) -> str:
        pattern = config['special_pattern']
        return re.sub(pattern, '', self.text)

    def _clean_text(self) -> None:
        self._clean_header_footer()
        text = re.sub(r'\[.*?]', '', self.text)
        text = re.sub('–*', '', text)
        text = re.sub('—', '', text)
        text = re.sub(r'\n', ' ', text)
        text = re.sub('←→', '', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(' ', ' ', text)
        text = re.sub('--', ' ', text)
        text = re.sub('\ufeff', '', text)
        text = re.sub('™', '', text)
        text = re.sub('\\*', '', text)
        self.text = text

    def _clean_header_footer(self) -> None:
        header = '\\*\\*\\* START OF .+ \\*\\*\\*'
        footer = '\\*\\*\\* END OF .+ \\*\\*\\*'

        if '*** START OF' in self.text:
            self.text = re.split(footer, re.split(header, self.text)[1])[0]

    def _sent_tokenize(self) -> list[str]:
        return nltk.sent_tokenize(self.text)

    def _lexical_attributes(self) -> dict:
        return {token.text: {'index': token.i,
                             'text': token.text,
                             'is_alpha': token.is_alpha,
                             'is_punct': token.is_punct,
                             'like_num': token.like_num,
                             'is_stop': token.is_stop,
                             'out_of_vocab': token.is_oov,
                             'part_of_speech': token.pos_,
                             'shape': token.shape_,
                             'dep': token.dep_,
                             'head.text': token.head.text,
                             'lemma': token.lemma_,
                             'tag': token.tag_,
                             'has_vector': token.has_vector,
                             'vector_norm': token.vector_norm}
                for token in self.doc}

    def word_lexical(self, word: str) -> dict:
        try:
            return {word: self.lexical[word]}
        except KeyError:
            return {}

    def _named_entities(self) -> dict:
        return {ent.text: {'start_char': ent.start_char,
                           'end_char': ent.end_char,
                           'label': ent.label_,
                           'label_explanation': spacy.explain(ent.label_)}
                for ent in self.doc.ents}

    def word_entity(self, word: str) -> dict:
        try:
            return {word: self.entities[word]}
        except KeyError:
            return {}

    def entities_to_df(self) -> pd.DataFrame:
        entities_df = pd.DataFrame()
        for ent in self.entities.keys():
            word_entity = self.word_entity(word=ent)
            word_lexical = self.word_lexical(word=ent)
            entity_data = [{**v1, **v2} for v1 in word_entity.values() for v2 in word_lexical.values()]
            temp_df = pd.DataFrame(entity_data)
            entities_df = pd.concat([entities_df, temp_df], ignore_index=True)
        return entities_df

    def lexical_to_df(self) -> pd.DataFrame:
        lexical_df = pd.DataFrame()
        for ent in self.lexical.keys():
            word_entity = self.word_lexical(word=ent)
            temp_df = pd.DataFrame(word_entity.values())
            lexical_df = pd.concat([lexical_df, temp_df], ignore_index=True)
        return lexical_df

    def create_doc(self) -> Doc:
        return nlp(self.text)

    def export_text_data(self, metadata_path: str) -> None:
        filename = self.filename.split('.')[0]
        os.makedirs(name=f'{metadata_path}/', exist_ok=True)

        logging.info(msg=f'Pickle data generation for {self.filename}: {datetime.now()}')
        save_to_pickle(self)
        logging.info(msg=f'Entities file generation for {self.filename}: {datetime.now()}')
        self.entities_to_df().to_csv(f'{metadata_path}/{filename}_entities.csv')
        logging.info(msg=f'Lexical file generation for {self.filename}: {datetime.now()}')
        self.lexical_to_df().to_csv(f'{metadata_path}/{filename}_lexical.csv')


def save_to_pickle(text_properties: TextProperties) -> None:
    filename = text_properties.filename.split('.')[0]
    with open(f"{config['metadata_folder']}{filename}/{filename}.pkl", 'wb') as file:
        pickle.dump(text_properties, file)


def load_from_pickle(path_to_text_properties: str) -> TextProperties:
    with open(path_to_text_properties, 'rb') as file:
        return pickle.load(file)


def export_batch(text_file: str, input_folder: str) -> None:
    data_path = f'{config["data_path"]}{input_folder}/{text_file}'
    metadata_path = f'{config["metadata_folder"]}{text_file.split(".")[0]}'

    if not os.path.isdir(metadata_path):
        text_prop = TextProperties(data_path)
        text_prop.export_text_data(metadata_path)


def exec() -> None:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--folder',
                        type=str,
                        default='20240404',
                        help='folder name in format: [YYYYmmdd]')

    args = vars(parser.parse_args())
    input_folder: str = args.get("folder")

    files = os.listdir(f'{config["data_path"]}/{input_folder}/')
    text_files = [file for file in files if file.endswith('.txt')]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_export = {executor.submit(export_batch, text_file, input_folder): text_file for text_file in text_files}

        for future in concurrent.futures.as_completed(future_export):
            export = future_export[future]
            try:
                future.result()
            except Exception as e:
                logging.error(msg='%r generated an exception: %s' % (export, e))


if __name__ == '__main__':
    exec()
