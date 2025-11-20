"""
SocketIO Chat Events
Handles chat streaming with vLLM integration.
"""

import logging
import random
import requests
from flask import request
from flask_socketio import emit
from openai import OpenAI


def register_chat_events(socketio, chat_manager):
    """Register chat-related SocketIO events"""

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
        ssh_container = "llars_docker_ssh_proxy_service"
        ssh_container_port = "8093"
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

            # Use vLLM via the OpenAI-compatible interface
            client = OpenAI(
                api_key="EMPTY",
                base_url=f"http://{ssh_container}:{ssh_container_port}/v1"
            )

            assistant_message = ""
            # Stream chat completion from vLLM
            stream = client.chat.completions.create(
                model="mistralai/Mistral-Small-3.1-24B-Instruct-2503",
                messages=[{"role": "user", "content": formatted_input}],
                temperature=temperature,
                max_tokens=chat_manager.prompt_manager.max_new_tokens,
                stream=True
            )

            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                content = getattr(delta, "content", "")
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
        """Handle test prompt streaming with optional JSON mode"""
        client_id = request.sid
        logging.info(f"handle_test_prompt_stream called. SID={client_id}, data={data}")
        user_prompt = data.get('prompt', '')

        # Initialize vLLM client
        ssh_container = "llars_docker_ssh_proxy_service"
        ssh_container_port = "8093"
        client = OpenAI(
            api_key="EMPTY",
            base_url=f"http://{ssh_container}:{ssh_container_port}/v1"
        )

        try:
            messages = [{"role": "user", "content": user_prompt}]

            # Optionaler JSON Mode: erzwungenes strukturierte JSON-Antworten
            json_mode = data.get('jsonMode', True)
            logging.info(f"handle_test_prompt_stream: JSON Mode = {json_mode}")

            # Bereite extra_body vor, nur wenn JSON Mode aktiviert
            if json_mode:
                # JSON Mode: use provided schema for guided_json
                schema = data.get('schema', {}) or {}
                extra_body = {
                    "guided_json": schema,
                    "guided_decoding_backend": "outlines"
                }
                extra_kwargs = {"extra_body": extra_body}
                logging.info(f"handle_test_prompt_stream: extra_kwargs={extra_kwargs}")
            else:
                extra_kwargs = {}
                logging.info("handle_test_prompt_stream: JSON Mode disabled, no extra_kwargs")

            # Stream test completion
            stream = client.chat.completions.create(
                model="mistralai/Mistral-Small-3.1-24B-Instruct-2503",
                messages=messages,
                max_tokens=4096,
                n=1,
                timeout=360.0,
                frequency_penalty=0.3,
                temperature=0.15,
                stream=True,
                **extra_kwargs
            )

            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                content = getattr(delta, "content", "")
                if content:
                    emit(
                        "test_prompt_response",
                        {"content": content, "complete": False},
                        room=client_id
                    )
                if getattr(choice, "finish_reason", None) is not None:
                    emit(
                        "test_prompt_response",
                        {"content": "", "complete": True},
                        room=client_id
                    )
                    break

        except Exception as e:
            logging.error(f"Test prompt stream error: {e}")
            emit(
                "test_prompt_response",
                {"content": f"Error: {e}", "complete": True},
                room=client_id
            )
