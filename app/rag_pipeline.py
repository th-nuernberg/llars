# rag_pipeline.py
import os
import logging
import hashlib
import threading
import json
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb

# Disable ChromaDB telemetry to avoid errors
os.environ["ANONYMIZED_TELEMETRY"] = "False"
chromadb.config.Settings(anonymized_telemetry=False)


DEFAULT_FALLBACK_EMBEDDING_MODEL = os.environ.get(
    "LLARS_FALLBACK_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)

# ChromaDB collection metadata for cosine distance
# IMPORTANT: This ensures proper similarity scoring for both normalized and unnormalized embeddings
CHROMA_COLLECTION_METADATA = {"hnsw:space": "cosine"}


class RAGPipeline:
    """
    RAG Pipeline with DB-driven embedding model selection.

    Embedding models are sourced from llm_models (model_type='embedding').
    """

    _shared_embeddings = None
    _shared_model_name = None
    _shared_model_type = None
    _shared_dimensions = None
    _shared_model_provider = None
    _embeddings_lock = threading.Lock()

    def __init__(self, docs_dir="docs", collection_name="llars_docs", storage_dir="/app/storage"):
        self.docs_dir = docs_dir
        self.storage_dir = storage_dir
        self.model_dir = os.path.join(storage_dir, "models")

        os.environ["HF_HOME"] = self.model_dir
        os.makedirs(self.model_dir, exist_ok=True)

        # Initialize embedding model (LiteLLM primary, HuggingFace fallback)
        self.embeddings, self.model_name, self.model_type, self.embedding_dimensions = self._init_embeddings()

        # Set up paths based on active model
        self.collection_name = f"{collection_name}_{self.model_name.replace('/', '_')}"
        self.vectorstore_dir = os.path.join(storage_dir, "vectorstore", self.model_name.replace('/', '_'))
        os.makedirs(self.vectorstore_dir, exist_ok=True)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["# ", "## ", "\n\n", "\n", ". ", "! ", "? "]
        )

        self.vectorstore = None

    def _init_embeddings(self):
        """
        Initialize embeddings with LiteLLM proxy as primary and HuggingFace as fallback.
        Returns: (embeddings, model_name, model_type, dimensions)
        """
        cached = self.__class__._shared_embeddings
        if cached is not None:
            return (
                cached,
                self.__class__._shared_model_name,
                self.__class__._shared_model_type,
                self.__class__._shared_dimensions
            )

        with self.__class__._embeddings_lock:
            cached = self.__class__._shared_embeddings
            if cached is not None:
                return (
                    cached,
                    self.__class__._shared_model_name,
                    self.__class__._shared_model_type,
                    self.__class__._shared_dimensions
                )

        litellm_api_key = os.environ.get("LITELLM_API_KEY")
        litellm_base_url = os.environ.get("LITELLM_BASE_URL")

        candidates = []
        app_context_available = False
        try:
            from flask import has_app_context
            app_context_available = has_app_context()
        except ImportError:
            pass

        if app_context_available:
            try:
                from db.models.llm_model import LLMModel

                candidates = (
                    LLMModel.query
                    .filter_by(model_type=LLMModel.MODEL_TYPE_EMBEDDING, is_active=True)
                    .order_by(LLMModel.is_default.desc(), LLMModel.display_name.asc())
                    .all()
                )
            except Exception as e:
                logging.error(f"[RAGPipeline] Failed to load embedding models from llm_models: {e}")
        else:
            logging.warning("[RAGPipeline] No Flask app context - using environment-based model selection")
            # When no app context, try LiteLLM with VDR-2B if configured
            env_model = os.environ.get("LLARS_EMBEDDING_MODEL", "llamaindex/vdr-2b-multi-v1")
            if litellm_api_key and litellm_base_url:
                # Create a synthetic candidate to try LiteLLM
                from types import SimpleNamespace
                candidates = [SimpleNamespace(model_id=env_model, provider="litellm")]

        def init_hf_embeddings(model_id: str, provider_label: str):
            try:
                logging.info(f"Initializing HuggingFace embedding model: {model_id}")

                # For models with custom code (like llamaindex/vdr-2b-multi-v1),
                # we need to add the model cache dir to sys.path so custom modules can be imported
                import sys
                cache_dirs = [
                    os.path.expanduser("~/.cache/huggingface/hub"),
                    self.model_dir,
                    "/app/storage/models"
                ]
                for cache_dir in cache_dirs:
                    if os.path.exists(cache_dir):
                        for root, dirs, files in os.walk(cache_dir):
                            if 'custom_st.py' in files and root not in sys.path:
                                logging.info(f"Adding custom module path: {root}")
                                sys.path.insert(0, root)

                embeddings = HuggingFaceEmbeddings(
                    model_name=model_id,
                    model_kwargs={"device": "cpu", "trust_remote_code": True},
                    encode_kwargs={"normalize_embeddings": True},
                    cache_folder=self.model_dir
                )
                test_result = embeddings.embed_query("test")
                if test_result and len(test_result) > 0:
                    dims = len(test_result)
                    logging.info(f"HuggingFace embedding model ready: {model_id} ({dims} dimensions)")
                    self.__class__._shared_embeddings = embeddings
                    self.__class__._shared_model_name = model_id
                    self.__class__._shared_model_type = "huggingface"
                    self.__class__._shared_dimensions = dims
                    self.__class__._shared_model_provider = provider_label
                    return embeddings, model_id, "huggingface", dims
            except Exception as e:
                logging.warning(f"[RAGPipeline] Failed to initialize HF embedding model {model_id}: {e}")
            return None

        if not candidates:
            logging.warning(
                "[RAGPipeline] No active embedding models configured in llm_models; using local fallback"
            )
            fallback = init_hf_embeddings(DEFAULT_FALLBACK_EMBEDDING_MODEL, "local-fallback")
            if fallback:
                return fallback
            raise RuntimeError("No active embedding models configured and fallback failed")

        # Models available via LiteLLM/KIZ - try API first
        litellm_embedding_models = ["llamaindex/vdr-2b-multi-v1"]

        def try_litellm_model(model_id: str, provider: str):
            """Try loading model via LiteLLM API.

            IMPORTANT: For VDR-2B multimodal model, we use LiteLLMDirectEmbeddings
            instead of langchain's OpenAIEmbeddings. This ensures consistency with
            how images are embedded (both use direct HTTP requests).
            """
            if not (litellm_api_key and litellm_base_url):
                return None

            # For VDR-2B multimodal model, use direct HTTP embeddings for consistency with images
            if model_id == "llamaindex/vdr-2b-multi-v1":
                try:
                    from services.rag.image_embedding_service import LiteLLMDirectEmbeddings

                    logging.info(f"[RAGPipeline] Using LiteLLMDirectEmbeddings for {model_id} (multimodal consistency)")
                    embeddings = LiteLLMDirectEmbeddings(model=model_id)
                    test_result = embeddings.embed_query("test")
                    if test_result and len(test_result) > 0:
                        dims = len(test_result)
                        logging.info(f"[RAGPipeline] LiteLLMDirectEmbeddings ready: {model_id} ({dims} dimensions)")
                        self.__class__._shared_embeddings = embeddings
                        self.__class__._shared_model_name = model_id
                        self.__class__._shared_model_type = "litellm"
                        self.__class__._shared_dimensions = dims
                        self.__class__._shared_model_provider = provider
                        return embeddings, model_id, "litellm", dims
                except Exception as e:
                    logging.warning(f"[RAGPipeline] LiteLLMDirectEmbeddings failed for {model_id}: {e}")
                    # Fall through to try OpenAIEmbeddings as backup

            # For other models, use langchain's OpenAIEmbeddings
            try:
                logging.info(f"[RAGPipeline] Attempting LiteLLM embedding model: {model_id}")
                embeddings = OpenAIEmbeddings(
                    model=model_id,
                    openai_api_key=litellm_api_key,
                    openai_api_base=litellm_base_url
                )
                test_result = embeddings.embed_query("test")
                if test_result and len(test_result) > 0:
                    dims = len(test_result)
                    logging.info(f"[RAGPipeline] LiteLLM embedding model ready: {model_id} ({dims} dimensions)")
                    self.__class__._shared_embeddings = embeddings
                    self.__class__._shared_model_name = model_id
                    self.__class__._shared_model_type = "litellm"
                    self.__class__._shared_dimensions = dims
                    self.__class__._shared_model_provider = provider
                    return embeddings, model_id, "litellm", dims
            except Exception as e:
                logging.warning(f"[RAGPipeline] LiteLLM failed for {model_id}: {e}")
            return None

        for model in candidates:
            model_id = model.model_id
            provider = (model.provider or "").lower()

            # Check if model is local-only (sentence-transformers)
            is_local_only = (
                provider in {"huggingface", "sentence-transformers", "local"}
                or model_id.startswith("sentence-transformers/")
            )

            # Check if model is available via LiteLLM/KIZ
            is_litellm_model = model_id in litellm_embedding_models

            # Strategy 1: Local-only models -> HuggingFace directly
            if is_local_only:
                result = init_hf_embeddings(model_id, model.provider or "huggingface")
                if result:
                    return result
                continue

            # Strategy 2: Models available via LiteLLM -> try API first, then local
            if is_litellm_model:
                result = try_litellm_model(model_id, model.provider or "litellm")
                if result:
                    return result
                logging.info(f"[RAGPipeline] LiteLLM unavailable for {model_id}, trying local HuggingFace")
                result = init_hf_embeddings(model_id, "huggingface-fallback")
                if result:
                    return result
                continue

            # Strategy 3: Other models -> try LiteLLM, then local
            result = try_litellm_model(model_id, model.provider or "litellm")
            if result:
                return result
            result = init_hf_embeddings(model_id, "huggingface-fallback")
            if result:
                return result

        fallback = init_hf_embeddings(DEFAULT_FALLBACK_EMBEDDING_MODEL, "local-fallback")
        if fallback:
            return fallback

        raise RuntimeError("Unable to initialize any embedding model from llm_models")

    @classmethod
    def clear_embedding_cache(cls):
        """
        Clear the cached embedding model.
        Use this to force re-initialization (e.g., after config changes).
        """
        with cls._embeddings_lock:
            cls._shared_embeddings = None
            cls._shared_model_name = None
            cls._shared_model_type = None
            cls._shared_dimensions = None
            cls._shared_model_provider = None
            logging.info("[RAGPipeline] Embedding cache cleared")

    @classmethod
    def is_using_fallback(cls) -> bool:
        """Check if currently using local fallback model."""
        return cls._shared_model_type == "huggingface" and cls._shared_model_provider == "local-fallback"

    def get_embedding_info(self):
        """
        Returns information about the current embedding model configuration.
        Useful for admin panel and debugging.
        """
        primary_model = None
        fallback_model = None
        try:
            from db.models.llm_model import LLMModel
            models = (
                LLMModel.query
                .filter_by(model_type=LLMModel.MODEL_TYPE_EMBEDDING, is_active=True)
                .order_by(LLMModel.is_default.desc(), LLMModel.display_name.asc())
                .all()
            )
            if models:
                primary_model = models[0].model_id
            for m in models[1:]:
                if m.model_id != self.model_name:
                    fallback_model = m.model_id
                    break
        except Exception:
            primary_model = None
            fallback_model = None

        if not fallback_model:
            fallback_model = DEFAULT_FALLBACK_EMBEDDING_MODEL

        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "provider": self.__class__._shared_model_provider,
            "dimensions": self.embedding_dimensions,
            "is_primary": self.model_type == "litellm",
            "primary_model": primary_model,
            "fallback_model": fallback_model,
            "litellm_configured": bool(os.environ.get("LITELLM_API_KEY") and os.environ.get("LITELLM_BASE_URL")),
            "litellm_base_url": os.environ.get("LITELLM_BASE_URL", "Not configured"),
            "vectorstore_dir": self.vectorstore_dir,
            "collection_name": self.collection_name
        }

    def _get_docs_hash(self):
        hash_md5 = hashlib.md5()
        for root, _, files in os.walk(self.docs_dir):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                with open(file_path, "rb") as f:
                    hash_md5.update(f.read())
        return hash_md5.hexdigest()

    def load_and_index_docs(self, allow_rebuild: bool = True):
        docs_hash_path = os.path.join(self.vectorstore_dir, "docs_hash.json")
        model_info_path = os.path.join(self.vectorstore_dir, "model_info.json")
        current_docs_hash = None

        has_saved_index = (
            os.path.exists(self.vectorstore_dir)
            and os.path.exists(docs_hash_path)
            and os.path.exists(model_info_path)
        )

        if has_saved_index:
            with open(model_info_path, "r") as f:
                saved_model = json.load(f).get("model_name")

            if saved_model == self.model_name and not allow_rebuild:
                logging.info("Attempting to load existing vectorstore (rebuild disabled)...")
                try:
                    self.vectorstore = Chroma(
                        collection_name=self.collection_name,
                        persist_directory=self.vectorstore_dir,
                        embedding_function=self.embeddings,
                        collection_metadata=CHROMA_COLLECTION_METADATA,
                    )
                    logging.info("Vectorstore loaded successfully")
                    return
                except Exception as e:
                    logging.error(f"Error loading vectorstore: {str(e)}")
                    return 0

            if saved_model == self.model_name:
                with open(docs_hash_path, "r") as f:
                    saved_docs_hash = json.load(f).get("hash")
                current_docs_hash = self._get_docs_hash()

                if saved_docs_hash == current_docs_hash:
                    logging.info("Attempting to load existing vectorstore...")
                    try:
                        self.vectorstore = Chroma(
                            collection_name=self.collection_name,
                            persist_directory=self.vectorstore_dir,
                            embedding_function=self.embeddings,
                            collection_metadata=CHROMA_COLLECTION_METADATA,
                        )
                        logging.info("Vectorstore loaded successfully")
                        return
                    except Exception as e:
                        logging.error(f"Error loading vectorstore: {str(e)}")

            if not allow_rebuild:
                logging.info(
                    "Vectorstore is missing or outdated and rebuild is disabled "
                    "(set RAG_PIPELINE_BUILD_ON_STARTUP=true to rebuild)."
                )
                return 0
        elif not allow_rebuild:
            logging.info(
                "No existing vectorstore found and rebuild is disabled "
                "(set RAG_PIPELINE_BUILD_ON_STARTUP=true to build)."
            )
            return 0

        logging.info(f"Creating new vectorstore for {self.model_name}")
        if current_docs_hash is None:
            current_docs_hash = self._get_docs_hash()
        if self.vectorstore:
            self.delete_index()

        documents = []
        loaded_files = 0
        logging.info("Starting document processing...")

        for root, _, files in os.walk(self.docs_dir):
            for file in files:
                if file.endswith(('.txt', '.md', '.pdf')):
                    file_path = os.path.join(root, file)
                    loaded_docs = self.load_document(file_path)
                    documents.extend(loaded_docs)
                    loaded_files += 1

        if not documents:
            logging.warning("No documents found")
            return 0

        splits = self.text_splitter.split_documents(documents)
        logging.info(f"Processing {loaded_files} files with total {len(splits)} chunks")

        try:
            self.vectorstore = Chroma.from_documents(
                documents=splits,
                collection_name=self.collection_name,
                persist_directory=self.vectorstore_dir,
                embedding=self.embeddings
            )

            with open(docs_hash_path, "w") as f:
                json.dump({"hash": current_docs_hash}, f)
            with open(model_info_path, "w") as f:
                json.dump({"model_name": self.model_name}, f)

            logging.info(f"Vectorstore created and {len(splits)} chunks indexed")
            return 0
        except Exception as e:
            logging.error(f"Error creating vectorstore: {str(e)}")
            raise

    def load_document(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()

        try:
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
                logging.info(f"Loading PDF: {file_path}")
                return loader.load()
            elif file_extension in ['.txt', '.md']:
                loader = TextLoader(file_path, encoding='utf-8')
                logging.info(f"Loading text file: {file_path}")
                return loader.load()
            else:
                logging.warning(f"Unsupported file type: {file_path}")
                return []
        except Exception as e:
            logging.error(f"Error loading {file_path}: {str(e)}")
            return []

    def delete_index(self):
        if self.vectorstore:
            try:
                self.vectorstore.delete_collection()
                self.vectorstore = None
                logging.info("Successfully deleted vector store collection")
            except Exception as e:
                logging.error(f"Error deleting vector store: {str(e)}")
                raise

    def get_rag_context(self, user_message, num_docs=4):
        """
        Retrieves the RAG context for the given query.
        Returns the concatenated text of relevant documents.
        """
        if not self.vectorstore:
            logging.warning("No vector store available for retrieval")
            return ""

        try:
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": num_docs}
            )

            docs = retriever.invoke(user_message)
            logging.info(f"Retrieved {len(docs)} documents for query")
            context = "\n\n".join([doc.page_content for doc in docs])
            return context
        except Exception as e:
            logging.error(f"Error retrieving documents: {str(e)}")
            return ""
