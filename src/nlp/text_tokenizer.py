import json
import pickle
import re
from dataclasses import dataclass, field
import nltk
import spacy
from spacy.tokens.doc import Doc

CONFIG_JSON = 'config/text_tokenizer.json'
nlp = spacy.load("en_core_web_lg")


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
        pattern = r'[a-zA-z0-9.,!?/:;\"\'\s]'
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
        return {token.text: [token.i,
                             token.text,
                             token.is_alpha,
                             token.is_punct,
                             token.like_num,
                             token.is_stop,
                             token.is_oov,
                             token.pos_,
                             token.dep_,
                             token.head.text,
                             token.lemma_,
                             token.tag_,
                             token.shape_,
                             token.has_vector,
                             token.vector_norm]
                for token in self.doc}

    def _named_entities(self) -> dict:
        return {ent.text: [ent.start_char, ent.end_char, ent.label_, spacy.explain(ent.label_)]
                for ent in self.doc.ents}

    def create_doc(self) -> Doc:
        return nlp(self.text)


def save_to_pickle(text_properties: TextProperties) -> None:
    json_data = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
    with open(f"{json_data['pickle_folder']}{text_properties.filename.split('.')[0]}.pkl", 'wb') as file:
        pickle.dump(text_properties, file)


def load_from_pickle(path_to_text_properties: str) -> TextProperties:
    with open(path_to_text_properties, 'rb') as file:
        return pickle.load(file)


if __name__ == '__main__':
    tp = load_from_pickle('data/pg103.pkl')
    print(tp.entities)
