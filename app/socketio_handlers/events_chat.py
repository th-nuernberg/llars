"""
SocketIO Chat Events
Handles chat streaming with LiteLLM Proxy integration.

Events:
    Client → Server:
        - chat_stream: Send a chat message for streaming response
        - test_prompt_stream: Test a prompt with optional JSON mode

    Server → Client:
        - chat_response: Streaming chat response chunks
        - test_prompt_response: Streaming test prompt response chunks

Integration:
    - Uses LiteLLM Proxy with DB-configured LLM models
    - Supports RAG context injection via chat_manager.rag_pipeline
    - Maintains chat history per client (request.sid)
"""

import logging
import random
import requests
from flask import request
from flask_socketio import emit
from llm.openai_utils import extract_delta_text
from db.models.llm_model import LLMModel
from services.llm.llm_client_factory import LLMClientFactory


def register_chat_events(socketio, chat_manager):
    """
    Register chat-related SocketIO events.

    Events:
        chat_stream: Handle user chat message with RAG and streaming response
        test_prompt_stream: Handle test prompt with optional JSON mode
    """

    # Error Messages for failed chat requests
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

    def send_error_message(client_id):
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

    @socketio.on("chat_stream")
    def handle_chat_stream(data):
        """Handle streaming chat with RAG context"""
        client_id = request.sid

        try:
            user_message = data.get("message", "").encode('utf-8').decode('utf-8')
            temperature = data.get("temperature", 0.15)

            # Command Handling
            if user_message.strip().startswith('/'):
                command = user_message.strip()[1:]
                if command == 'clear':
                    chat_manager.clear_history(client_id)
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

            model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
            if not model_id:
                raise RuntimeError("No default LLM model configured in llm_models")
            client = LLMClientFactory.get_client_for_model(model_id)

            assistant_message = ""
            # Stream chat completion from LiteLLM Proxy
            metadata = {"tags": ["Technische Hochschule Nürnberg", "KIA"]}
            stream = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": formatted_input}],
                temperature=temperature,
                max_tokens=chat_manager.prompt_manager.max_new_tokens,
                stream=True,
                extra_body={"metadata": metadata}
            )

            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                content = extract_delta_text(delta)
                if content:
                    assistant_message += content
                    emit("chat_response", {
                        "content": content,
                        "complete": False,
                        "sender": "bot"
                    }, room=client_id)

                # If this chunk signals the end of the stream, emit completion
                if getattr(choice, "finish_reason", None) is not None:
                    emit("chat_response", {
                        "content": "",
                        "complete": True,
                        "sender": "bot"
                    }, room=client_id)
                    break

            # Persist the full assistant response
            chat_manager.add_to_history(client_id, "assistant", assistant_message)

        except requests.RequestException as e:
            logging.error(f"Request exception: {e}")
            send_error_message(client_id)

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            send_error_message(client_id)

    @socketio.on('test_prompt_stream')
    def handle_test_prompt_stream(data):
        """Handle test prompt streaming with optional JSON mode and configurable parameters"""
        client_id = request.sid
        logging.info(f"handle_test_prompt_stream called. SID={client_id}")
        user_prompt = data.get('prompt', '')

        # Get configurable parameters from frontend
        model = data.get('model')
        temperature = data.get('temperature', 0.15)
        max_tokens = data.get('maxTokens', 4096)

        if model:
            db_model = LLMModel.get_by_model_id(str(model).strip())
            if not db_model or not db_model.is_active or db_model.model_type != LLMModel.MODEL_TYPE_LLM:
                model = None

        if not model:
            model = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
            if not model:
                raise RuntimeError("No default LLM model configured in llm_models")

        # Validate parameters
        temperature = max(0.0, min(1.0, float(temperature)))
        max_tokens = max(100, min(8192, int(max_tokens)))

        logging.info(f"handle_test_prompt_stream: model={model}, temp={temperature}, max_tokens={max_tokens}")

        client = LLMClientFactory.get_client_for_model(model)

        try:
            messages = [{"role": "user", "content": user_prompt}]

            # Optionaler JSON Mode: erzwungenes strukturierte JSON-Antworten
            json_mode = data.get('jsonMode', True)
            logging.info(f"handle_test_prompt_stream: JSON Mode = {json_mode}")

            # Metadata für TH Nürnberg / KIA
            metadata = {"tags": ["Technische Hochschule Nürnberg", "KIA"]}

            # Bereite extra_body vor mit Metadata
            extra_body = {"metadata": metadata}

            if json_mode:
                # JSON Mode: use provided schema for guided_json
                schema = data.get('schema', {}) or {}
                # Only add guided_json if schema is not empty and has keys
                if schema and len(schema) > 0:
                    extra_body["guided_json"] = schema
                    logging.info(f"handle_test_prompt_stream: JSON Mode with schema: {schema}")
                else:
                    # Basic JSON mode - just request JSON output without guided schema
                    # Note: response_format may not be supported by all models
                    logging.info(f"handle_test_prompt_stream: JSON Mode (basic, no schema)")
            else:
                logging.info("handle_test_prompt_stream: JSON Mode disabled")

            extra_kwargs = {"extra_body": extra_body}

            logging.info(f"handle_test_prompt_stream: Starting stream with extra_body keys: {list(extra_body.keys())}")

            # Stream test completion from LiteLLM Proxy
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                n=1,
                timeout=360.0,
                frequency_penalty=0.3,
                temperature=temperature,
                stream=True,
                **extra_kwargs
            )

            logging.info("handle_test_prompt_stream: Stream created, starting iteration")
            chunk_count = 0

            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                content = extract_delta_text(delta)
                if content:
                    chunk_count += 1
                    if chunk_count <= 3:
                        logging.info(f"handle_test_prompt_stream: Emitting chunk {chunk_count}: {content[:50]}...")
                    emit(
                        "test_prompt_response",
                        {"content": content, "complete": False},
                        room=client_id
                    )
                if getattr(choice, "finish_reason", None) is not None:
                    logging.info(f"handle_test_prompt_stream: Stream complete, total chunks: {chunk_count}")
                    emit(
                        "test_prompt_response",
                        {"content": "", "complete": True},
                        room=client_id
                    )
                    break

        except Exception as e:
            logging.error(f"Test prompt stream error: {e}")
            # Send error message to client
            emit(
                "test_prompt_response",
                {"content": f"\n\nFehler: {str(e)[:200]}", "complete": True},
                room=client_id
            )
