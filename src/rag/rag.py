import json
from dataclasses import dataclass, field
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.response.pprint_utils import pprint_response
from llama_index.llms.ollama import Ollama
from llama_index.core.prompts.prompts import SimpleInputPrompt
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index.embeddings.langchain import LangchainEmbedding
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.node_parser import TokenTextSplitter

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
        self.output_path = json_data['output_path']
        self.embed_model = LangchainEmbedding(HuggingFaceEmbeddings(model_name=json_data['embedding_model']))

        self._create_model(
            model_version=json_data['model_version'],
            query_wrapper=json_data['query_wrapper'],
            system_prompt=json_data['system_prompt']
        )

        self._generate_docs()
        self._generate_metadata(json_data['metadata_path'])

        Settings.llm = self.model
        Settings.embed_model = self.embed_model
        Settings.node_parser = SentenceSplitter(chunk_size=json_data['chunk_size'], chunk_overlap=20)
        Settings.num_output = 512
        Settings.context_window = 3900

        transformations = [
            TokenTextSplitter(chunk_size=512, chunk_overlap=128),
        ]
        self.index = VectorStoreIndex.from_documents(documents=self.docs,
                                                     embed_model=self.embed_model, transformations=transformations)

        self.query_engine = self.index.as_query_engine()

    def _generate_docs(self):
        self.docs = SimpleDirectoryReader(self.path).load_data()

    def _generate_metadata(self, path: str):
        self.metadata = [doc.metadata for doc in self.docs]
        with open(path, 'w') as metadata:
            json.dump(self.metadata, fp=metadata)

    def _create_model(self, model_version: str, query_wrapper: str, system_prompt: str):
        self.model = Ollama(model=model_version,
                            query_wrapper_prompt=SimpleInputPrompt(query_wrapper),
                            system_prompt=system_prompt)

    def query(self, question: str):
        response = self.query_engine.query(question)
        source_text = response.get_formatted_sources(length=200)
        output_string = "Response: {}\nSources:\n{}".format(response, source_text)
        with open(f'{self.output_path}/output.txt', 'w') as output:
            output.write(output_string)

        pprint_response(response, show_source=True)


if __name__ == '__main__':
    rag = RAG()

    while True:
        print("Write your query: ")
        query_input = input('> ')
        if query_input == 'exit':
            break
        rag.query(query_input)
        print()
