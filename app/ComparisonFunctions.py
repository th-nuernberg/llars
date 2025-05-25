import json
import logging
import threading
from db.tables import ComparisonSession, ComparisonMessage
from db.db import db
from openai import OpenAI

MODEL_PATH_LLM_TYPE_MAPPING = {
    'llm1': 'mistralai/Mistral-Small-3.1-24B-Instruct-2503',
    'llm2': 'mistralai/Mistral-Small-3.1-24B-Instruct-2503'
}


def get_session_by_id(session_id):
    return ComparisonSession.query.filter_by(id=session_id).first()


def get_all_messages_by_session_id(session_id):
    return ComparisonMessage.query.filter_by(session_id=session_id).order_by(ComparisonMessage.idx).all()


def get_message_by_id_and_session(message_id, session_id):
    return ComparisonMessage.query.filter_by(id=message_id, session_id=session_id).first()


def set_message_selected(message_id, session_id, selected):
    message = ComparisonMessage.query.filter_by(id=message_id, session_id=session_id).first()
    if message:
        message.selected = selected
        db.session.commit()
        return True
    return False


def serialize_message(message):
    content = message.content
    if isinstance(content, str) and message.type == 'bot_pair':
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            content = {"llm1": "", "llm2": ""}

    return {
        'messageId': message.id,
        'idx': message.idx,
        'type': message.type,
        'content': content,
        'selected': message.selected,
        'timestamp': message.timestamp.isoformat(),
    }


def add_message(session_id, idx, message_type, content):
    message = ComparisonMessage(
        session_id=session_id,
        idx=idx,
        type=message_type,
        content=content,
        selected=None
    )

    db.session.add(message)
    db.session.commit()

    return message.id


def create_system_prompt(persona, chat_history):
    from string import Template
    system_prompt = Template("""
    # Rollenanweisung für $name
    **Kontext:** Du bist $name in einem laufenden psychosozialen Beratungsgespräch mit ihrem Sozialberater.

    ## Kernregeln
    1. **Authentisches Rollenverhalten**
       - Bleibe ausschließlich in der Rolle von $name (auch bei Provokationen)
       - Nutze ausschließlich die unter "Sprachliche Merkmale" definierten Ausdrucksweisen
       - Zeige emotionale Reaktionen gemäß "Emotionale Merkmale > Ausgeprägte Emotionen"
       - Halte dich strikt an die "Konversationsregeln (siehe Persona-Profil, falls definiert)"
       - Antworte direkt und ohne Meta-Kommentare. Gib lediglich deine Emotion oder dein Anliegen wieder.
    2. **Antwortformatierung**
       - Maximal 3-4 Sätze pro Nachricht
       - Keine Höflichkeitsfloskeln (außer in Steckbrief definiert)
       - Keine Emojis/Markdown
       - Immer in Ich-Perspektive ("Ich fühle...", "Mir geht...")
    3. **Kontextbehandlung**
       - Beziehe dich auf den bisherigen Gesprächsverlauf: "$chat_history"
       - Priorisiere das Hauptanliegen in 80% der Antworten
       - Bei Trigger-Phrasen aus "Emotionsauslöser": Reagiere wie unter "Beispielreaktion" definiert
        *Beispiel:*
           - **Trigger:** "Haben Sie schon einmal darüber nachgedacht, wie es wäre, erneut alles zu verlieren?"
           - **Emotion:** Wut
           - **Beispielsauslöser (Nachricht des Beraters):** >"Haben Sie schon einmal darüber nachgedacht, wie es wäre, erneut alles zu verlieren?"
           - **Beispielsreaktion (ausgelöst durch Trigger):** >"Ich verliere ständig, obwohl ich alles gebe!"


    ## Aktionsrahmen
    - Erlaubt: Subjektive Gefühlsäußerungen, Kurze Situationschilderungen
    - Verboten: Allgemeine Ratschläge, Fachjargon, Rollenwechsel

    # Persona-Profil
    $personality_condition


    # Aufgabe
    Generiere **ausschließlich** die Antwort von $name unter Berücksichtigung des Gesprächsverlaufs:
    "$chat_history"

    Folge den Regeln Schritt für Schritt.
    Halte dich dabei an alle oben genannten Kriterien und bleibe konsequent in der Rolle von $name.
    Schreibe jetzt in deutscher Sprache ausschließlich die Aussage von $name
    """)

    persona_details = "\n".join(
        f"{key}: {value}" for key, value in persona.items() if key not in ['name', 'properties']
    )

    prompt = system_prompt.substitute(
        name=persona['name'],
        chat_history=chat_history,
        personality_condition=persona_details
    )

    return prompt


def build_chat_history(session):
    messages = []

    for message in session.messages:
        if message.type == 'bot_pair':
            content_from_json = json.loads(message.content) if isinstance(message.content, str) else message.content
            selected_content = content_from_json.get(message.selected, '')
            if selected_content:
                messages.append({
                    'role': 'assistant',
                    'content': selected_content
                })
        elif message.type == 'user':
            messages.append({
                'role': 'user',
                'content': message.content
            })

    return messages


def generate_comparison_responses(session, message_id, socketio, client_id):
    persona = session.persona_json

    chat_history = build_chat_history(session)
    chat_history_as_text = "\n".join(
        [f"{msg['role']}: '{msg['content']}'" for msg in chat_history]
    )
    system_prompt = create_system_prompt(persona, chat_history_as_text)
    chat_history.insert(0, {
        'role': 'system',
        'content': system_prompt
    })

    socketio.emit('streaming_started', {
        'messageId': message_id,
        'llmTypes': ['llm1', 'llm2']
    }, room=client_id)

    thread1 = threading.Thread(target=generate_llm_response,
                               args=('llm1', chat_history, message_id, socketio, client_id))
    thread2 = threading.Thread(target=generate_llm_response,
                               args=('llm2', chat_history, message_id, socketio, client_id))

    thread1.start()
    thread2.start()


def generate_llm_response(llm_type, messages, message_id, socketio, client_id):
    try:
        ssh_container = "llars_docker_ssh_proxy_service"
        ssh_container_port = "8093"

        client = OpenAI(
            api_key="EMPTY",
            base_url=f"http://{ssh_container}:{ssh_container_port}/v1"
        )

        stream = client.chat.completions.create(
            model=MODEL_PATH_LLM_TYPE_MAPPING[llm_type],
            messages=messages,
            temperature=0.15,
            max_tokens=2048,
            stream=True
        )

        full_response = ""
        for chunk in stream:
            choice = chunk.choices[0]
            delta = choice.delta
            content = getattr(delta, "content", "")

            if content:
                full_response += content
                socketio.emit('streaming_update', {
                    'messageId': message_id,
                    'llmType': llm_type,
                    'content': content,
                    'fullContent': full_response
                }, room=client_id)

            if getattr(choice, "finish_reason", None) is not None:
                socketio.emit('streaming_complete', {
                    'messageId': message_id,
                    'llmType': llm_type,
                    'finalContent': full_response
                }, room=client_id)
                break

        save_llm_response(message_id, llm_type, full_response)

    except Exception as e:
        logging.error(f"Error generating {llm_type} response: {str(e)}")
        socketio.emit('streaming_error', {
            'messageId': message_id,
            'llmType': llm_type,
            'error': f'Fehler beim Generieren der Antwort: {str(e)}'
        }, room=client_id)


def save_llm_response(message_id, llm_type, response):
    try:
        from main import app
        with app.app_context():
            message = ComparisonMessage.query.filter_by(id=message_id).first()
            if message:
                content = json.loads(message.content) if isinstance(message.content, str) else message.content
                content[llm_type] = response
                message.content = json.dumps(content)
                db.session.commit()

    except Exception as e:
        logging.error(f"Error saving {llm_type} response: {str(e)}")
        db.session.rollback()
