import json
from dataclasses import dataclass, field
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.core.prompts.prompts import SimpleInputPrompt
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index.core import ServiceContext
from llama_index.embeddings.langchain import LangchainEmbedding
import pickle as pkl

CONFIG_JSON = 'config/rag_config.json'


@dataclass
class RAG:
    docs: list = field(init=False)
    model: Ollama = field(init=False)
    index: VectorStoreIndex = field(init=False)
    metadata: list = field(default_factory=list)

    def __post_init__(self):
        json_data = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
        self.path = json_data['data_path']
        self.embed_model = LangchainEmbedding(HuggingFaceEmbeddings(model_name=json_data['embedding_model']))

        self._create_model(
            model_version=json_data['model_version'],
            query_wrapper=json_data['query_wrapper'],
            system_prompt=json_data['system_prompt']
        )

        self._generate_docs()
        self._generate_metadata()

        self.service_context = ServiceContext.from_defaults(
            chunk_size=json_data['chunk_size'],
            llm=self.model,
            embed_model=self.embed_model
        )

        self.index = VectorStoreIndex.from_documents(self.docs, service_context=self.service_context)

    def _generate_docs(self):
        self.docs = SimpleDirectoryReader(self.path).load_data()

    def _generate_metadata(self):
        self.metadata = [doc.metadata for doc in self.docs]

    def _create_model(self, model_version: str, query_wrapper: str, system_prompt: str):
        self.model = Ollama(model=model_version,
                            query_wrapper_prompt=SimpleInputPrompt(query_wrapper),
                            system_prompt=system_prompt)

    def query(self, question: str):
        query_engine = self.index.as_query_engine()
        return query_engine.query(question)

    @staticmethod
    def save_rag_to_pickle(rag_to_save, path_to_pickle: str = 'config/rag_file.pkl'):
        with open(path_to_pickle, mode='wb') as rag_file:
            pkl.dump(rag_to_save, rag_file)

        rag_file.close()

    @staticmethod
    def load_rag_from_pickle(path_to_pickle: str = 'config/rag_file.pkl'):
        with open(path_to_pickle, mode='rb') as rag_file:
            return pkl.load(rag_file)


if __name__ == '__main__':
    rag = RAG()
    print(rag.query("¿Quién es el padre de Pinoccio y cuáles son sus características?").response)
