from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os
import logging
from pathlib import Path
import hashlib
import json

class RAGPipeline:
    def __init__(self, docs_dir="docs", collection_name="llars_docs", storage_dir="/app/storage"):
        self.docs_dir = docs_dir
        self.collection_name = collection_name
        self.model_dir = os.path.join(storage_dir, "models")
        self.vectorstore_dir = os.path.join(storage_dir, "vectorstore")

        os.environ["HF_HOME"] = self.model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.vectorstore_dir, exist_ok=True)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            cache_folder=self.model_dir
        )

        self.vectorstore = None

    def _get_docs_hash(self):
        hash_md5 = hashlib.md5()
        for root, _, files in os.walk(self.docs_dir):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                with open(file_path, "rb") as f:
                    hash_md5.update(f.read())
        return hash_md5.hexdigest()

    def load_and_index_docs(self):
        docs_hash_path = os.path.join(self.vectorstore_dir, "docs_hash.json")
        current_docs_hash = self._get_docs_hash()

        if os.path.exists(self.vectorstore_dir) and os.path.exists(docs_hash_path):
            with open(docs_hash_path, "r") as f:
                saved_docs_hash = json.load(f).get("hash")

            if saved_docs_hash == current_docs_hash:
                logging.info("No changes in documents. Loading existing vector store...")
                self.vectorstore = Chroma(
                    persist_directory=self.vectorstore_dir,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings
                )
                return len(self.vectorstore.get())

        logging.info("Changes detected in documents. Reindexing...")
        documents = []
        for root, _, files in os.walk(self.docs_dir):
            for file in files:
                if file.endswith(('.txt', '.md', '.pdf')):
                    file_path = os.path.join(root, file)
                    documents.extend(self.load_document(file_path))

        if not documents:
            logging.warning("No documents were loaded.")
            return 0

        splits = self.text_splitter.split_documents(documents)
        logging.info(f"Split documents into {len(splits)} chunks.")

        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding_function=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=self.vectorstore_dir
        )
        self.vectorstore.persist()

        with open(docs_hash_path, "w") as f:
            json.dump({"hash": current_docs_hash}, f)

        return len(splits)

    def load_document(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()

        try:
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
                logging.info(f"Loading PDF: {file_path}")
                return loader.load()
            elif file_extension in ['.txt', '.md']:
                loader = TextLoader(file_path)
                logging.info(f"Loading text file: {file_path}")
                return loader.load()
            else:
                logging.warning(f"Unsupported file type: {file_path}")
                return []
        except Exception as e:
            logging.error(f"Error loading {file_path}: {str(e)}")
            return []

    def enrich_prompt(self, user_message, system_prompt, num_docs=3):
        if not self.vectorstore:
            logging.warning("No vector store available for retrieval")
            return system_prompt

        try:
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": num_docs}
            )

            docs = retriever.invoke(user_message)
            context = "\n\n".join([doc.page_content for doc in docs])
            enriched_prompt = f"\n{context}\n"

            logging.info("Successfully enriched prompt with context")
            return enriched_prompt
        except Exception as e:
            logging.error(f"Error enriching prompt: {str(e)}")
            return system_prompt

    def delete_index(self):
        if self.vectorstore:
            try:
                self.vectorstore.delete_collection()
                self.vectorstore = None
                logging.info("Successfully deleted vector store collection")
            except Exception as e:
                logging.error(f"Error deleting vector store: {str(e)}langchain_huggingface")
                raise

    def get_relevant_docs(self, query, num_docs=3):
        if not self.vectorstore:
            logging.warning("No vector store available for retrieval")
            return []

        try:
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": num_docs}
            )

            docs = retriever.invoke(query)
            logging.info(f"Retrieved {len(docs)} documents for query")
            return docs
        except Exception as e:
            logging.error(f"Error retrieving documents: {str(e)}")
            return []