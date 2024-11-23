from flask_socketio import emit
from flask import request
import json
import requests
import logging
from prompt_manager import PromptManager
from rag_pipeline import RAGPipeline

# Erweitere Logging-Format für bessere Lesbarkeit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ChatManager:
    def __init__(self,
                 system_prompt_path: str = "/app/prompts/system_prompt.txt",
                 docs_dir: str = "/app/rag_docs",
                 verbose: bool = False):
        self.prompt_manager = PromptManager(system_prompt_path=system_prompt_path)
        self.rag_pipeline = self._initialize_rag(docs_dir)
        self.chat_histories = {}  # Speichert Chat-Historien pro Client
        self.verbose = verbose

    def _initialize_rag(self, docs_dir: str) -> RAGPipeline:
        """Initialisiert die RAG Pipeline."""
        try:
            rag = RAGPipeline(docs_dir=docs_dir)
            rag.load_and_index_docs()
            return rag
        except Exception as e:
            logging.error(f"Failed to initialize RAG pipeline: {str(e)}")
            return None

    def get_chat_history(self, client_id: str) -> list:
        """Holt die Chat-Historie für einen Client."""
        return self.chat_histories.get(client_id, [])

    def add_to_history(self, client_id: str, role: str, content: str):
        """Fügt eine neue Nachricht zur Chat-Historie hinzu."""
        if client_id not in self.chat_histories:
            self.chat_histories[client_id] = []

        self.chat_histories[client_id].append({
            'role': role,
            'content': content
        })

    def clear_history(self, client_id: str):
        """Löscht die Chat-Historie eines Clients."""
        self.chat_histories[client_id] = []

    def log_prompt_details(self, prompt: str, rag_context: str = "", chat_history: list = None):
        """Loggt detaillierte Informationen über das Prompt wenn verbose aktiviert ist."""
        if not self.verbose:
            return

        logging.info("\n" + "=" * 50 + " PROMPT DETAILS " + "=" * 50)

        # System Prompt
        logging.info("\n----- SYSTEM PROMPT -----")
        logging.info(self.prompt_manager.system_prompt)

        # RAG Kontext
        if rag_context:
            logging.info("\n----- RAG CONTEXT -----")
            logging.info(rag_context)

        # Chat Historie
        if chat_history:
            logging.info("\n----- CHAT HISTORY -----")
            for msg in chat_history:
                logging.info(f"[{msg['role']}]: {msg['content']}")

        # Vollständiges Prompt
        logging.info("\n----- COMPLETE PROMPT -----")
        logging.info(prompt)

        # Prompt Statistiken
        logging.info("\n----- PROMPT STATISTICS -----")
        logging.info(f"Total length (chars): {len(prompt)}")
        logging.info(f"Estimated tokens: {len(prompt) // 4}")

        logging.info("=" * 120 + "\n")


def configure_socket_routes(socketio, verbose=True):
    chat_manager = ChatManager(verbose=verbose)

    @socketio.on('connect')
    def handle_connect():
        emit('welcome', {
            'message': 'Welcome to LLARS Chat!',
            'client_id': request.sid
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        chat_manager.clear_history(request.sid)
        logging.info(f'Client {request.sid} disconnected')

    @socketio.on("chat_stream")
    def handle_chat_stream(data):
        ssh_container = "llars_docker_ssh_proxy_service"
        ssh_container_port = "8093"

        user_message = data.get("message", "").encode('utf-8').decode('utf-8')
        temperature = data.get("temperature", 0.7)
        client_id = request.sid

        # Füge User Message zur Historie hinzu
        chat_manager.add_to_history(client_id, "user", user_message)

        try:
            # Hole RAG Kontext
            rag_context = ""
            if chat_manager.rag_pipeline:
                rag_context = chat_manager.rag_pipeline.enrich_prompt(user_message, "")
                logging.info(f"RAG context retrieved: {len(rag_context)} chars")

            # Hole Chat-Historie
            chat_history = chat_manager.get_chat_history(client_id)

            # Erstelle formatiertes Prompt
            formatted_input = chat_manager.prompt_manager.create_prompt(
                current_message=user_message,
                chat_history=chat_history,
                rag_context=rag_context
            )

            # Log Prompt Details wenn verbose aktiviert
            chat_manager.log_prompt_details(
                prompt=formatted_input,
                rag_context=rag_context,
                chat_history=chat_history
            )

            payload = {
                "inputs": formatted_input,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": chat_manager.prompt_manager.max_new_tokens,
                    "top_p": 0.95,
                    "top_k": 50,
                    "repetition_penalty": 1.1,
                    "do_sample": True,
                    "return_full_text": False,
                    "stop": ["[INST]", "</s>"]
                }
            }

            # Sammle die komplette Antwort für die Historie
            complete_response = []

            with requests.post(
                    f"http://{ssh_container}:{ssh_container_port}/generate_stream",
                    json=payload,
                    stream=True,
                    timeout=30,
                    headers={'Content-Type': 'application/json; charset=utf-8'}
            ) as response:
                response.encoding = 'utf-8'
                if response.status_code == 200:
                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.startswith("data:"):
                            try:
                                json_data = json.loads(line[5:])

                                if json_data.get("generated_text"):
                                    final_text = json_data["generated_text"]
                                    complete_response.append(final_text)
                                    # Füge vollständige Antwort zur Historie hinzu
                                    chat_manager.add_to_history(client_id, "assistant", final_text)
                                    emit("chat_response", {
                                        "content": final_text,
                                        "complete": True
                                    }, room=client_id)
                                    break

                                if "token" in json_data and "text" in json_data["token"]:
                                    content = json_data["token"]["text"].encode('utf-8').decode('utf-8')
                                    complete_response.append(content)
                                    emit("chat_response", {
                                        "content": content,
                                        "complete": False
                                    }, room=client_id)

                            except json.JSONDecodeError:
                                logging.warning(f"Failed to parse JSON: {line}")
                                continue

                    emit("chat_response", {
                        "content": "",
                        "complete": True
                    }, room=client_id)
                else:
                    error_msg = "Error during streaming."
                    chat_manager.add_to_history(client_id, "system", error_msg)
                    emit("chat_response", {
                        "content": error_msg,
                        "complete": True
                    }, room=client_id)

        except requests.RequestException as e:
            error_msg = "Error: Unable to stream response."
            chat_manager.add_to_history(client_id, "system", error_msg)
            logging.error(f"Request exception: {e}")
            emit("chat_response", {
                "content": error_msg,
                "complete": True
            }, room=client_id)