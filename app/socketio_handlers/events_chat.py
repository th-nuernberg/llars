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
import time
from typing import Optional
from flask import request
from flask_socketio import emit
from llm.openai_utils import extract_delta_text
from services.llm.llm_client_factory import LLMClientFactory


def _is_openai_model(model_id: Optional[str], api_model_id: Optional[str]) -> bool:
    """Check if a model is an OpenAI model (requires max_completion_tokens)."""
    mid = (model_id or "").lower()
    api_mid = (api_model_id or "").lower()
    return 'openai' in mid or api_mid.startswith('gpt-') or api_mid.startswith('o')


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

            resolve_start = time.perf_counter()
            client, api_model = LLMClientFactory.resolve_for_chat(None)
            resolve_ms = (time.perf_counter() - resolve_start) * 1000
            if not client:
                raise RuntimeError("No default LLM model configured in llm_models")
            logging.info(f"chat_stream: resolve_for_chat took {resolve_ms:.1f}ms, api_model={api_model}")

            # OpenAI models require max_completion_tokens instead of max_tokens
            token_param = ("max_completion_tokens" if _is_openai_model(api_model, api_model)
                           else "max_tokens")

            assistant_message = ""
            # Stream chat completion from LiteLLM Proxy
            metadata = {"tags": ["Technische Hochschule Nürnberg", "KIA"]}
            create_start = time.perf_counter()
            stream = client.chat.completions.create(
                model=api_model,
                messages=[{"role": "user", "content": formatted_input}],
                temperature=temperature,
                **{token_param: chat_manager.prompt_manager.max_new_tokens},
                stream=True,
                extra_body={"metadata": metadata}
            )
            create_ms = (time.perf_counter() - create_start) * 1000
            logging.info(f"chat_stream: create() returned after {create_ms:.1f}ms")

            first_token_logged = False
            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                content = extract_delta_text(delta)
                if content:
                    if not first_token_logged:
                        ttfb_ms = (time.perf_counter() - create_start) * 1000
                        logging.info(f"chat_stream: first token after {ttfb_ms:.1f}ms")
                        first_token_logged = True
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

        # Validate parameters
        temperature = max(0.0, min(1.0, float(temperature)))
        max_tokens = max(100, min(8192, int(max_tokens)))

        # Single cached call: validates model, falls back to default, resolves client.
        # Avoids 4-6 redundant DB queries that previously ran on every request.
        # User-provider models (user-provider:<id>:...) keep their unique API keys.
        resolve_start = time.perf_counter()
        client, api_model_id = LLMClientFactory.resolve_for_chat(model)
        resolve_ms = (time.perf_counter() - resolve_start) * 1000
        if not client:
            logging.error("No default LLM model configured in llm_models")
            emit(
                "test_prompt_response",
                {"content": "Fehler: Kein Standard-LLM-Modell konfiguriert. Bitte kontaktieren Sie den Administrator.", "complete": True},
                room=client_id
            )
            return
        logging.info(f"handle_test_prompt_stream: resolve_for_chat took {resolve_ms:.1f}ms")
        logging.info(f"handle_test_prompt_stream: model={model}, api_model={api_model_id}, temp={temperature}, max_tokens={max_tokens}")

        try:
            messages = [{"role": "user", "content": user_prompt}]

            # Optionaler JSON Mode: erzwungenes strukturierte JSON-Antworten
            json_mode = data.get('jsonMode', True)
            logging.info(f"handle_test_prompt_stream: JSON Mode = {json_mode}")

            is_openai = _is_openai_model(model, api_model_id)

            # Build extra_body only with compatible params
            extra_body = {}

            # Metadata only for LiteLLM proxy (OpenAI API rejects array-typed tags)
            if not is_openai:
                extra_body["metadata"] = {"tags": ["Technische Hochschule Nürnberg", "KIA"]}

            if json_mode:
                schema = data.get('schema', {}) or {}
                if schema and len(schema) > 0:
                    extra_body["guided_json"] = schema
                    logging.info(f"handle_test_prompt_stream: JSON Mode with schema: {schema}")
                else:
                    logging.info(f"handle_test_prompt_stream: JSON Mode (basic, no schema)")
            else:
                logging.info("handle_test_prompt_stream: JSON Mode disabled")

            extra_kwargs = {"extra_body": extra_body} if extra_body else {}

            logging.info(f"handle_test_prompt_stream: Starting stream with extra_body keys: {list(extra_body.keys())}")

            # OpenAI models require max_completion_tokens instead of max_tokens
            token_param = ("max_completion_tokens" if _is_openai_model(model, api_model_id)
                           else "max_tokens")

            # Stream test completion
            create_start = time.perf_counter()
            stream = client.chat.completions.create(
                model=api_model_id,
                messages=messages,
                **{token_param: max_tokens},
                n=1,
                timeout=360.0,
                frequency_penalty=0.3,
                temperature=temperature,
                stream=True,
                **extra_kwargs
            )
            create_ms = (time.perf_counter() - create_start) * 1000
            logging.info(f"handle_test_prompt_stream: create() returned after {create_ms:.1f}ms")

            logging.info("handle_test_prompt_stream: Stream created, starting iteration")
            chunk_count = 0
            first_token_logged = False

            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                content = extract_delta_text(delta)
                if content:
                    if not first_token_logged:
                        ttfb_ms = (time.perf_counter() - create_start) * 1000
                        logging.info(f"handle_test_prompt_stream: first token after {ttfb_ms:.1f}ms")
                        first_token_logged = True
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
