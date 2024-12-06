# routes_socketio.py
from flask_socketio import emit
from flask import request
import json
import requests
import logging
import random
from prompt_manager import PromptManager
from rag_pipeline import RAGPipeline

# Enhanced logging format
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
        self.chat_histories = {}  # Stores chat histories per client
        self.verbose = verbose

    def _initialize_rag(self, docs_dir: str) -> RAGPipeline:
        """Initializes the RAG Pipeline."""
        try:
            rag = RAGPipeline(docs_dir=docs_dir)
            rag.load_and_index_docs()
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


def configure_socket_routes(socketio, verbose=True):
    chat_manager = ChatManager(verbose=verbose)

    @socketio.on('connect')
    def handle_connect():
        client_id = request.sid
        username = request.args.get('username', 'Gast')
        logging.info(f'Client {client_id} connected')

        # Get existing chat history for the client
        existing_history = chat_manager.get_chat_history(client_id)

        # Only send welcome message if there's no existing history
        if not existing_history:
            initial_message = f"Hallo {username}! Wie kann ich dir helfen?"
            chat_manager.add_to_history(client_id, 'bot', initial_message)
            emit('chat_response', {
                'content': initial_message,
                'complete': True,
                'sender': 'bot'
            }, room=client_id)

    @socketio.on('disconnect')
    def handle_disconnect():
        chat_manager.clear_history(request.sid)
        logging.info(f'Client {request.sid} disconnected')

    @socketio.on("chat_stream")
    def handle_chat_stream(data):
        ssh_container = "llars_docker_ssh_proxy_service"
        ssh_container_port = "8093"
        client_id = request.sid

        # Error Messages
        ERROR_MESSAGES = [
            "Tut mir leid, ich mache gerade ein kurzes Nickerchen. Versuche es in ein paar Minuten noch einmal!",
            "Oh je, meine Gehirnzellen streiken gerade. Ich brauche einen Moment zum Aufwärmen.",
            "Hmm, scheint als hätte ich gerade eine kleine Denkpause. Gleich bin ich wieder fit!",
            "Entschuldige, ich bin gerade in einer wichtigen Meditation. Komme gleich zurück!",
            "Ups, meine neuronalen Netze haben sich verheddert. Gib mir kurz Zeit zum Entwirren.",
            "Sorry, ich musste kurz einen Bärenschlaf machen. Bin gleich wieder da!",
            "Meine KI-Synapsen brauchen einen Moment zum Synchronisieren. Gleich geht's weiter!",
            "Technische Pause - ich sortiere gerade meine Gedanken. Bin in Kürze wieder für dich da!",
            "Da hat wohl jemand meinen Stecker gezogen. Keine Sorge, ich bin gleich wieder online!",
            "Zeit für eine kurze Verschnaufpause. Ich sammle neue Energie für unsere Unterhaltung!"
        ]

        def send_error_message():
            """Hilfsfunktion zum Senden von Fehlermeldungen mit Stream-Simulation"""
            error_msg = random.choice(ERROR_MESSAGES)
            retry_msg = "Versuche es einfach in ein paar Minuten noch einmal."

            # Teile die Hauptfehlermeldung in Chunks auf
            chunks = []
            current_chunk = ""
            words = error_msg.split()

            for word in words:
                if len(current_chunk) < 10:
                    current_chunk += word + " "
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = word + " "
            if current_chunk:
                chunks.append(current_chunk.strip())

            # Sende die Chunks mit Verzögerung
            for chunk in chunks:
                emit("chat_response", {
                    "content": chunk + " ",
                    "complete": False,
                    "sender": "bot"
                }, room=client_id)
                socketio.sleep(0.1)

            # Kurze Pause vor der Retry-Nachricht
            socketio.sleep(0.5)

            # Sende Retry-Nachricht
            retry_chunks = retry_msg.split()
            for word in retry_chunks:
                emit("chat_response", {
                    "content": word + " ",
                    "complete": False,
                    "sender": "bot"
                }, room=client_id)
                socketio.sleep(0.2)

            # Abschließende Nachricht als complete
            emit("chat_response", {
                "content": "",
                "complete": True,
                "sender": "bot"
            }, room=client_id)

            # Füge zur Chat-Historie hinzu
            chat_manager.add_to_history(client_id, "bot", f"{error_msg} {retry_msg}")

        try:
            user_message = data.get("message", "").encode('utf-8').decode('utf-8')
            temperature = data.get("temperature", 0.6)

            # Command Handling
            if user_message.strip().startswith('/'):
                command = user_message.strip()[1:]
                if command == 'clear':
                    chat_manager.clear_history(client_id)
                    # Send confirmation message
                    emit('chat_response', {
                        'content': 'Der Chat-Verlauf wurde gelöscht.',
                        'complete': True,
                        'sender': 'bot'
                    }, room=client_id)
                    return
                else:
                    emit('chat_response', {
                        'content': f'Unbekannter Befehl: {command}',
                        'complete': True,
                        'sender': 'bot'
                    }, room=client_id)
                    return

            # Add User Message to History
            chat_manager.add_to_history(client_id, "user", user_message)

            # Get RAG Context
            rag_context = ""
            if chat_manager.rag_pipeline:
                try:
                    rag_context = chat_manager.rag_pipeline.get_rag_context(user_message, num_docs=4)
                    logging.info(f"RAG context retrieved: {len(rag_context)} chars")
                except Exception as e:
                    logging.error(f"RAG pipeline error: {e}")

            # Get Chat History
            chat_history = chat_manager.get_chat_history(client_id)

            # Create formatted prompt
            formatted_input = chat_manager.prompt_manager.create_prompt(
                chat_history=chat_history,
                rag_context=rag_context
            )

            # Log Prompt Details if verbose is enabled
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

            response = requests.post(
                f"http://{ssh_container}:{ssh_container_port}/generate_stream",
                json=payload,
                stream=True,
                timeout=30,
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )

            response.encoding = 'utf-8'
            if response.status_code == 200:
                assistant_message = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        try:
                            json_data = json.loads(line[5:])

                            if json_data.get("generated_text"):
                                final_text = json_data["generated_text"]
                                assistant_message += final_text
                                chat_manager.add_to_history(client_id, "assistant", assistant_message)
                                emit("chat_response", {
                                    "content": final_text,
                                    "complete": True,
                                    "sender": "bot"
                                }, room=client_id)
                                break

                            if "token" in json_data and "text" in json_data["token"]:
                                content = json_data["token"]["text"].encode('utf-8').decode('utf-8')
                                assistant_message += content
                                emit("chat_response", {
                                    "content": content,
                                    "complete": False,
                                    "sender": "bot"
                                }, room=client_id)

                        except json.JSONDecodeError:
                            logging.warning(f"Failed to parse JSON: {line}")
                            continue
                else:
                    # Add assistant message to history if not already added
                    if assistant_message:
                        chat_manager.add_to_history(client_id, "assistant", assistant_message)
            else:
                logging.error(f"Error response from LLM service: {response.status_code}")
                send_error_message()

        except requests.RequestException as e:
            logging.error(f"Request exception: {e}")
            send_error_message()

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            send_error_message()
