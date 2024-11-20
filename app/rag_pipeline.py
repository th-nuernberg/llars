from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma  # Korrigierter Import
import os
import logging


class RAGPipeline:
    def __init__(self, docs_dir="docs", collection_name="llars_docs"):
        """
        Initialize the RAG pipeline.

        Args:
            docs_dir (str): Directory containing the documentation files
            collection_name (str): Name for the Chroma collection
        """
        self.docs_dir = docs_dir
        self.collection_name = collection_name
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        # Initialize embedding model
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': True}

        logging.info(f"Initializing embeddings with model: {model_name}")
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
        except Exception as e:
            logging.error(f"Failed to initialize embeddings: {str(e)}")
            raise

        self.vectorstore = None

    def load_document(self, file_path):
        """
        Load a single document based on its file extension.

        Args:
            file_path (str): Path to the document

        Returns:
            list: List of Document objects
        """
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

    def load_and_index_docs(self):
        """Load and index all documents from the docs directory."""
        if not os.path.exists(self.docs_dir):
            logging.error(f"Documents directory {self.docs_dir} does not exist")
            raise FileNotFoundError(f"Directory not found: {self.docs_dir}")

        documents = []
        logging.info(f"Loading documents from {self.docs_dir}")

        # Walk through docs directory
        for root, _, files in os.walk(self.docs_dir):
            for file in files:
                if file.endswith(('.txt', '.md', '.pdf')):
                    file_path = os.path.join(root, file)
                    documents.extend(self.load_document(file_path))

        if not documents:
            logging.warning("No documents were loaded")
            return 0

        # Split documents
        try:
            splits = self.text_splitter.split_documents(documents)
            logging.info(f"Split documents into {len(splits)} chunks")
        except Exception as e:
            logging.error(f"Error splitting documents: {str(e)}")
            raise

        # Create or update vector store
        try:
            self.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                collection_name=self.collection_name
            )
            logging.info("Successfully created vector store")
        except Exception as e:
            logging.error(f"Error creating vector store: {str(e)}")
            raise

        return len(splits)

    def enrich_prompt(self, user_message, system_prompt, num_docs=3):
        """
        Enrich the given prompt with relevant context from the indexed documents.

        Args:
            user_message (str): The user's message
            system_prompt (str): The original system prompt
            num_docs (int): Number of relevant documents to retrieve

        Returns:
            str: Enriched prompt with relevant context
        """
        if not self.vectorstore:
            logging.warning("No vector store available for retrieval")
            return system_prompt

        try:
            # Create retriever
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": num_docs}
            )

            # Retrieve relevant documents
            docs = retriever.invoke(user_message)

            # Extract relevant context
            context = "\n\n".join([doc.page_content for doc in docs])

            # Add context to system prompt
            enriched_prompt = f"""
            {system_prompt}

            Relevanter Kontext aus der Dokumentation:
            {context}
            """

            logging.info("Successfully enriched prompt with context")
            return enriched_prompt
        except Exception as e:
            logging.error(f"Error enriching prompt: {str(e)}")
            return system_prompt
    def delete_index(self):
        """Delete the vector store collection."""
        if self.vectorstore:
            try:
                self.vectorstore.delete_collection()
                self.vectorstore = None
                logging.info("Successfully deleted vector store collection")
            except Exception as e:
                logging.error(f"Error deleting vector store: {str(e)}")
                raise

    def get_relevant_docs(self, query, num_docs=3):
        """
        Retrieve relevant documents for a given query.

        Args:
            query (str): The search query
            num_docs (int): Number of documents to retrieve

        Returns:
            list: List of retrieved documents
        """
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