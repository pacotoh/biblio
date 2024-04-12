import re
from dataclasses import dataclass, field
from typing import ClassVar
import nltk
import spacy
from spacy.pipeline.senter import Language


@dataclass
class TextProperties:
    text: str = field(default='', init=True)
    nlp: ClassVar[Language] = spacy.load("en_core_web_sm")
    sentences: list = field(default_factory=list, init=False)
    tokens: list = field(default_factory=list, init=False)
    entities: dict = field(default_factory=dict, init=False)
    lexical: dict = field(default_factory=dict, init=False)
    special_chars: str = field(init=False)

    def __post_init__(self):
        self.doc = TextProperties.nlp(self.text)
        self.lexical = self._lexical_attributes()
        self._sent_tokenize()
        self._named_entities()
        self._special_characters()

    def _special_characters(self):
        pattern = r'[a-zA-z0-9.,!?/:;\"\'\s]'
        self.special_chars = re.sub(pattern, '', self.text)

    def _clean_text(self):
        text = re.sub(r'\[.*?\]', '', self.text)
        text = re.sub('–*', '', text)
        text = re.sub('—', '', text)
        text = re.sub(r'\n', ' ', text)
        text = re.sub('←→', '', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(' ', ' ', text)
        self.text = text

    def _sent_tokenize(self):
        self.sentences = nltk.sent_tokenize(self.text)

    def _lexical_attributes(self) -> dict:
        return {token.text: [token.i,
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

    def _named_entities(self):
        self.entities = {ent.text: [ent.start_char, ent.end_char, ent.label_, spacy.explain(ent.label_)]
                         for ent in self.doc.ents}

    def save_to_pickle(self):
        pass

    def load_from_pickle(self):
        pass


if __name__ == '__main__':
    tp = TextProperties('This is an example. And this is another example speaking about Frank in New York.')
    print(tp)
