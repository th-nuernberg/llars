"""
Chat Manager for SocketIO
Handles RAG pipeline, prompt management, and chat history.
"""

import logging
import os
from prompt_manager import PromptManager
from rag_pipeline import RAGPipeline


class ChatManager:
    """Manages chat functionality including RAG and prompt handling"""

    def __init__(self,
                 system_prompt_path: str = "/app/prompts/system_prompt.txt",
                 docs_dir: str = "/app/rag_docs",
                 verbose: bool = False):
        self.prompt_manager = PromptManager(system_prompt_path=system_prompt_path)
        self.rag_pipeline = self._initialize_rag(docs_dir)
        self.chat_histories = {}  # Stores chat histories per client
        self.verbose = verbose

    def _initialize_rag(self, docs_dir: str) -> RAGPipeline:
        """Initializes the RAG Pipeline."""
        try:
            rag = RAGPipeline(docs_dir=docs_dir)
            build_on_startup = os.environ.get("RAG_PIPELINE_BUILD_ON_STARTUP", "false").strip().lower() in (
                "1", "true", "yes", "on"
            )
            rag.load_and_index_docs(allow_rebuild=build_on_startup)
            return rag
        except Exception as e:
            logging.error(f"Failed to initialize RAG pipeline: {str(e)}")
            return None

    def get_chat_history(self, client_id: str) -> list:
        """Gets the chat history for a client."""
        return self.chat_histories.get(client_id, [])

    def add_to_history(self, client_id: str, role: str, content: str):
        """Adds a new message to the chat history."""
        if client_id not in self.chat_histories:
            self.chat_histories[client_id] = []

        self.chat_histories[client_id].append({
            'role': role,
            'content': content
        })

    def clear_history(self, client_id: str):
        """Clears the chat history of a client."""
        self.chat_histories[client_id] = []

    def log_prompt_details(self, prompt: str, rag_context: str = "", chat_history: list = None):
        """Logs detailed information about the prompt if verbose is enabled."""
        if not self.verbose:
            return

        logging.info("\n" + "=" * 50 + " PROMPT DETAILS " + "=" * 50)

        # System Prompt
        logging.info("\n----- SYSTEM PROMPT -----")
        logging.info(self.prompt_manager.system_prompt)

        # RAG Context
        if rag_context:
            logging.info("\n----- RAG CONTEXT -----")
            logging.info(rag_context)

        # Chat History
        if chat_history:
            logging.info("\n----- CHAT HISTORY -----")
            for msg in chat_history:
                logging.info(f"[{msg['role']}]: {msg['content']}")

        # Full Prompt
        logging.info("\n----- COMPLETE PROMPT -----")
        logging.info(prompt)

        # Prompt Statistics
        logging.info("\n----- PROMPT STATISTICS -----")
        logging.info(f"Total length (chars): {len(prompt)}")
        logging.info(f"Estimated tokens: {len(prompt) // 4}")

        logging.info("=" * 120 + "\n")
