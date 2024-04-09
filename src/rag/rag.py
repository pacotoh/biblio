import json
from dataclasses import dataclass, field
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.core.prompts.prompts import SimpleInputPrompt
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index.core import ServiceContext
from llama_index.embeddings.langchain import LangchainEmbedding

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


if __name__ == '__main__':
    rag = RAG()

    while True:
        print("Write your query: ")
        query_input = input('> ')
        if query_input == 'exit':
            break
        print(f'Answer: {rag.query(query_input)}')
        print()
