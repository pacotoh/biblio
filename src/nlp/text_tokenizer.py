import json
import pickle
import re
from dataclasses import dataclass, field
import nltk
import spacy
from spacy.tokens.doc import Doc
import pandas as pd

CONFIG_JSON = 'config/text_tokenizer.json'
config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
nlp = spacy.load(config['spacy_model'])


@dataclass
class TextProperties:
    path: str = field(init=True)
    text: str = field(default='', init=False)
    sentences: list = field(default_factory=list, init=False)
    tokens: list = field(default_factory=list, init=False)
    entities: dict = field(default_factory=dict, init=False)
    lexical: dict = field(default_factory=dict, init=False)
    special_chars: str = field(init=False)

    def __post_init__(self):
        with open(self.path, 'r') as file:
            self.text = file.read()

        self.filename = self.path.split('/')[-1]
        self._clean_text()
        self.doc = nlp(self.text)
        self.lexical = self._lexical_attributes()
        self.sentences = self._sent_tokenize()
        self.entities = self._named_entities()
        self.special_chars = self._special_characters()
        self.verbs_lemma = set([token.lemma_ for token in self.doc if token.pos_ == "VERB"])

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['doc']
        return state

    def _special_characters(self) -> str:
        pattern = config['special_pattern']
        return re.sub(pattern, '', self.text)

    def _clean_text(self):
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

    def _clean_header_footer(self):
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
            word_entity = tp.word_entity(word=ent)
            word_lexical = tp.word_lexical(word=ent)
            entity_data = [{**v1, **v2} for v1 in word_entity.values() for v2 in word_lexical.values()]
            temp_df = pd.DataFrame(entity_data)
            entities_df = pd.concat([entities_df, temp_df], ignore_index=True)
        return entities_df

    def lexical_to_df(self) -> pd.DataFrame:
        lexical_df = pd.DataFrame()
        for ent in self.lexical.keys():
            word_entity = tp.word_lexical(word=ent)
            temp_df = pd.DataFrame(word_entity.values())
            lexical_df = pd.concat([lexical_df, temp_df], ignore_index=True)
        return lexical_df

    def create_doc(self) -> Doc:
        return nlp(self.text)


def save_to_pickle(text_properties: TextProperties) -> None:
    with open(f"{config['pickle_folder']}{text_properties.filename.split('.')[0]}.pkl", 'wb') as file:
        pickle.dump(text_properties, file)


def load_from_pickle(path_to_text_properties: str) -> TextProperties:
    with open(path_to_text_properties, 'rb') as file:
        return pickle.load(file)


if __name__ == '__main__':
    # tp = TextProperties(path='../../data/wk/20240404/1st_Hum_Awards.txt')
    tp = load_from_pickle('data/1st_Hum_Awards.pkl')
    tp.entities_to_df().to_csv('data/1st_Hum_Awards_entities.csv')
    tp.lexical_to_df().to_csv('data/1st_Hum_Awards_lexical.csv')
