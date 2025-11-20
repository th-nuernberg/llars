from db.tables import ComparisonSession, ComparisonMessage, ComparisonEvaluation
from db.db import db
from openai import OpenAI
from single_message_evaluation import SingleEvaluator
import json
import logging
import threading


def get_model_mapping_for_session(session):
    try:
        from db.tables import RatingScenarios
        scenario = RatingScenarios.query.filter_by(id=session.scenario_id).first()
        
        if scenario and scenario.llm1_model and scenario.llm2_model:
            return {
                'llm1': scenario.llm1_model,
                'llm2': scenario.llm2_model
            }
        else:
            raise ValueError("No valid model mapping found for the session or scenario.")
    except Exception as e:
        logging.error(f"Error getting model mapping: {str(e)}")
        raise ValueError(f"Error accessing scenario data: {str(e)}")

def get_session_by_id(session_id):
    from sqlalchemy.orm import joinedload
    return ComparisonSession.query.options(joinedload(ComparisonSession.scenario)).filter_by(id=session_id).first()


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


def perform_ai_evaluation(message_id, session_id, user_selection):
    try:
        evaluation = ComparisonEvaluation.query.filter_by(message_id=message_id).order_by(ComparisonEvaluation.timestamp.desc()).first()
        
        if not evaluation:
            logging.warning(f"No AI evaluation found for message {message_id}, performing now...")
            return perform_ai_evaluation_fallback(message_id, session_id, user_selection)
        
        evaluation.user_selection = user_selection
        ai_selection = evaluation.ai_selection
        
        matches = check_rating_match(user_selection, ai_selection)
        evaluation.match_result = matches
        
        db.session.commit()
        
        return matches, {
            'ai_selection': ai_selection,
            'ai_reason': evaluation.ai_reason,
            'user_selection': user_selection
        }
        
    except Exception as e:
        logging.error(f"Error in AI evaluation check: {str(e)}")
        return True, None


def perform_ai_evaluation_fallback(message_id, session_id, user_selection):
    try:
        message = ComparisonMessage.query.filter_by(id=message_id, session_id=session_id).first()
        if not message or message.type != 'bot_pair':
            return True, None
            
        session = ComparisonSession.query.filter_by(id=session_id).first()
        if not session:
            return True, None
            
        content = message.content
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                logging.error(f"Could not parse message content for evaluation: {message_id}")
                return True, None
                
        if not isinstance(content, dict) or 'llm1' not in content or 'llm2' not in content:
            return True, None
            
        chat_history = build_chat_history_for_evaluation(session, message.idx)
        
        persona_description = format_persona_info(session.persona_json) if session.persona_json else "Keine Persona-Information verfügbar"
        
        evaluator = SingleEvaluator()
        result = evaluator.evaluate_responses(
            persona_description=persona_description,
            history=chat_history,
            response1=content['llm1'],
            response2=content['llm2']
        )
        
        ai_selection = map_ai_rating_to_selection(result.get('rating', 'error'))
        ai_reason = result.get('reason', 'Keine Begründung verfügbar')
        
        matches = check_rating_match(user_selection, ai_selection)
        
        evaluation = ComparisonEvaluation(
            message_id=message_id,
            user_selection=user_selection,
            ai_selection=ai_selection,
            ai_reason=ai_reason,
            match_result=matches
        )
        
        db.session.add(evaluation)
        db.session.commit()
        
        return matches, {
            'ai_selection': ai_selection,
            'ai_reason': ai_reason,
            'user_selection': user_selection
        }
        
    except Exception as e:
        logging.error(f"Error in AI evaluation fallback: {str(e)}")
        return True, None


def build_chat_history_for_evaluation(session, up_to_idx):
    messages = ComparisonMessage.query.filter_by(session_id=session.id).filter(ComparisonMessage.idx < up_to_idx).order_by(ComparisonMessage.idx).all()
    
    history_parts = []
    for msg in messages:
        if msg.type == 'user':
            history_parts.append(f"Berater: {msg.content}")
        elif msg.type == 'bot_pair' and msg.selected:
            content = msg.content
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    continue
            
            if isinstance(content, dict) and msg.selected in content:
                history_parts.append(f"Klient: {content[msg.selected]}")
    
    return "\n".join(history_parts)


def map_ai_rating_to_selection(ai_rating):
    if ai_rating == 'model_1':
        return 'llm1'
    elif ai_rating == 'model_2':
        return 'llm2'
    elif ai_rating == 'same':
        return 'tie'
    else:
        return 'error'


def check_rating_match(user_selection, ai_selection):
    if ai_selection == 'error':
        return True
    
    return user_selection == ai_selection


def save_user_justification(message_id, justification):
    try:
        evaluation = ComparisonEvaluation.query.filter_by(message_id=message_id).order_by(ComparisonEvaluation.timestamp.desc()).first()
        if evaluation:
            evaluation.user_justification = justification
            db.session.commit()
            return True
        return False
    except Exception as e:
        logging.error(f"Error saving user justification: {str(e)}")
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


def format_persona_info(persona):
    if not persona or not isinstance(persona, dict):
        return ""
    
    output = f"## Persona: {persona.get('name', 'Unknown')}\n\n"
    
    properties = persona.get('properties', {})
    
    if 'Steckbrief' in properties and properties['Steckbrief']:
        steckbrief = properties['Steckbrief']
        if isinstance(steckbrief, dict):
            output += "**Steckbrief:**\n"
            for key, value in steckbrief.items():
                output += f"- **{key}**: {value}\n"
            output += "\n"
        else:
            logging.warning(f"Steckbrief is not a dict but {type(steckbrief)}: {steckbrief}")
    
    if 'Hauptanliegen' in properties and properties['Hauptanliegen']:
        hauptanliegen = properties['Hauptanliegen']
        bullets = hauptanliegen.replace('. ', '.\n- ')
        output += f"**Hauptanliegen**\n- {bullets}\n\n"
    
    optional_sections = {
        'Nebenanliegen': 'Nebenanliegen',
        'Sprachliche Merkmale': 'Sprachliche Merkmale'
    }
    
    for key, title in optional_sections.items():
        if key in properties and properties[key]:
            output += f"**{title}**\n"
            items = properties[key] if isinstance(properties[key], list) else [properties[key]]
            for item in items:
                output += f"- {item}\n"
            output += "\n"
    
    if 'Emotionale Merkmale' in properties and properties['Emotionale Merkmale']:
        emotionale_merkmale = properties['Emotionale Merkmale']
        output += "**Emotionale Merkmale:**\n"
        
        if 'Grundhaltung' in emotionale_merkmale:
            output += f"- **Emotionale Grundhaltung zu Beginn des Gesprächs**: {emotionale_merkmale['Grundhaltung']}.\n"
        
        if 'ausgepraegte Emotionen' in emotionale_merkmale:
            output += f"- **Ausgeprägte Emotionen** bei {persona.get('name', 'der Persona')}:\n"
            for emotion in emotionale_merkmale['ausgepraegte Emotionen']:
                output += f"- {emotion}\n"
        
        if 'details' in emotionale_merkmale:
            details = emotionale_merkmale['details']
            if isinstance(details, dict):
                for emotion, emotion_details in details.items():
                    if isinstance(emotion_details, dict) and 'ausloeser' in emotion_details and 'reaktion' in emotion_details:
                        output += f"  - **{emotion}**:\n"
                        ausloeser = emotion_details.get('ausloeser', 'n/a')
                        reaktion = emotion_details.get('reaktion', '')
                        output += f"    - Die Emotion {emotion} wird bei {persona.get('name', 'der Persona')} durch {ausloeser} ausgelöst und löst folgende Reaktion aus: {reaktion}. "
                        
                        if 'beispielsausloeser' in emotion_details:
                            output += f"-Beispielnachrichten des Beraters (mögliche Auslöser für diese Emotion) {emotion}:>\"{emotion_details['beispielsausloeser']}\".\n"
                        
                        if 'beispielsreaktion' in emotion_details:
                            output += f"-Beispielsreaktion der Persona für {emotion}:>\"{emotion_details['beispielsreaktion']}\".\n"
                        else:
                            output += "\n"
            else:
                logging.warning(f"details is not a dict but {type(details)}: {details}")
        output += "\n"
    
    if 'Ressourcen' in properties and properties['Ressourcen']:
        ressourcen = properties['Ressourcen']
        output += "**Folgende Ressourcen stehen der Persona zur Verfügung:**\n"
        output += f"- Emotional (Fähigkeit, mit Gefühlen und Stress umzugehen): {'Ja' if ressourcen.get('emotional') else 'Nein'}\n"
        output += f"- Sozial (Unterstützung durch Familie, Freunde, Netzwerke): {'Ja' if ressourcen.get('sozial') else 'Nein'}\n"
        output += f"- Finanziell (Verfügbarkeit von Geld oder materiellen Mitteln): {'Ja' if ressourcen.get('finanziell') else 'Nein'}\n"
        
        andere_text = "Ja" if ressourcen.get('andere') else "Nein"
        if ressourcen.get('andere') and ressourcen.get('andereDetails'):
            andere_text += f" ({ressourcen['andereDetails']})"
        output += f"- Andere: {andere_text}\n\n"
    
    if 'Soziales Umfeld' in properties and properties['Soziales Umfeld']:
        output += "**Soziales Umfeld**\n"
        soziales_umfeld = properties['Soziales Umfeld']
        if isinstance(soziales_umfeld, str):
            for item in soziales_umfeld.split(', '):
                output += f"- {item.strip()}\n"
        elif isinstance(soziales_umfeld, list):
            for item in soziales_umfeld:
                output += f"- {item}\n"
    
    if 'Prinzipien' in properties and properties['Prinzipien']:
        output += "**Konversationsprinzipien**\n"
        prinzipien = properties['Prinzipien'] if isinstance(properties['Prinzipien'], list) else [properties['Prinzipien']]
        for prinzip in prinzipien:
            formatted_prinzip = prinzip.strip().replace('.', '.\n  - ')
            output += f"- {formatted_prinzip}\n"
    
    return output


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
    $persona_details


    # Aufgabe
    Generiere **ausschließlich** die Antwort von $name unter Berücksichtigung des Gesprächsverlaufs:
    "$chat_history"

    Folge den Regeln Schritt für Schritt.
    Halte dich dabei an alle oben genannten Kriterien und bleibe konsequent in der Rolle von $name.
    Schreibe jetzt in deutscher Sprache ausschließlich die Aussage von $name
    """)

    persona_details = format_persona_info(persona)

    prompt = system_prompt.substitute(
        name=persona['name'],
        chat_history=chat_history,
        persona_details=persona_details
    )

    is_first_message = not chat_history
    if is_first_message:
        prompt = f"{prompt}\n\n**Hinweis:** Dies ist die erste Nachricht in diesem Gespräch und du beginnst. Halte dich dabei an die sprachlichen Merkmale und die emotionale Grundhaltung, die in deinem Persona-Profil definiert sind."

    return prompt


def build_chat_history(session):
    messages = []
    
    try:
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
    except Exception as e:
        logging.error(f"Error building chat history: {str(e)}")

    return messages


def generate_comparison_responses(session, message_id, socketio, client_id):
    try:
        session_id = session.id
        
        from main import app
        with app.app_context():
            fresh_session = get_session_by_id(session_id)
            if not fresh_session:
                raise ValueError(f"Session with ID {session_id} not found")
            
            persona = fresh_session.persona_json
            chat_history = build_chat_history(fresh_session)
            chat_history_as_text = "\n".join(
                [f"{msg['role']}: '{msg['content']}'" for msg in chat_history]
            )
            system_prompt = create_system_prompt(persona, chat_history_as_text)

            socketio.emit('streaming_started', {
                'messageId': message_id,
                'llmTypes': ['llm1', 'llm2']
            }, room=client_id)

            is_first_message = not chat_history

            thread1 = threading.Thread(target=generate_llm_response,
                                       args=('llm1', system_prompt, is_first_message, message_id, socketio, client_id, session_id))
            thread2 = threading.Thread(target=generate_llm_response,
                                       args=('llm2', system_prompt, is_first_message, message_id, socketio, client_id, session_id))

            thread1.start()
            thread2.start()
    except Exception as e:
        logging.error(f"Error in generate_comparison_responses: {str(e)}")
        socketio.emit('streaming_error', {
            'messageId': message_id,
            'error': f'Fehler beim Generieren der Antwort: {str(e)}'
        }, room=client_id)


def generate_llm_response(llm_type, message, is_first_message, message_id, socketio, client_id, session_id):
    try:
        ssh_container = "llars_docker_ssh_proxy_service_2"
        ssh_container_port = "8195"

        client = OpenAI(
            api_key="EMPTY",
            base_url=f"http://{ssh_container}:{ssh_container_port}/v1"
        )

        from main import app
        with app.app_context():
            session = get_session_by_id(session_id)
            if not session:
                raise ValueError(f"Session with ID {session_id} not found")
            
            model_mapping = get_model_mapping_for_session(session)
            model_name = model_mapping.get(llm_type)

        stream = client.chat.completions.create(
            model=model_name,
            messages=[{
                    'role': 'system',
                    'content': message
            }],
            temperature=0.7,
            max_tokens=50 if is_first_message else 100,
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
                
                if 'llm1' in content and 'llm2' in content and content['llm1'] and content['llm2']:
                    perform_ai_evaluation_async(message_id, message.session_id)

    except Exception as e:
        logging.error(f"Error saving {llm_type} response: {str(e)}")
        db.session.rollback()


def generate_counselor_suggestion(session):
    try:
        session_id = session.id
        
        from main import app
        with app.app_context():
            fresh_session = get_session_by_id(session_id)
            if not fresh_session:
                raise ValueError(f"Session with ID {session_id} not found")
            
            persona = fresh_session.persona_json
            chat_history = build_chat_history(fresh_session)
            
            suggestion_prompt = create_counselor_suggestion_prompt(persona, chat_history)
            
            ssh_container = "llars_docker_ssh_proxy_service"
            ssh_container_port = "8093"

            client = OpenAI(
                api_key="EMPTY",
                base_url=f"http://{ssh_container}:{ssh_container_port}/v1"
            )

            response = client.chat.completions.create(
                model='mistralai/Mistral-Small-3.1-24B-Instruct-2503',
                messages=[{
                    'role': 'system',
                    'content': suggestion_prompt
                }],
                temperature=0.2,
                max_tokens=150
            )

            suggestion = response.choices[0].message.content.strip()
            return suggestion
        
    except Exception as e:
        logging.error(f"Error generating counselor suggestion: {str(e)}")
        return "Wie fühlen Sie sich in dieser Situation?"


def create_counselor_suggestion_prompt(persona, chat_history):
    persona_info = ""
    if persona and isinstance(persona, dict):
        if 'properties' in persona:
            props = persona['properties']
            if 'Hauptanliegen' in props:
                persona_info += f"Hauptanliegen: {props['Hauptanliegen']}\n"
            if 'Nebenanliegen' in props and props['Nebenanliegen']:
                persona_info += f"Nebenanliegen: {', '.join(props['Nebenanliegen'])}\n"
            if 'Steckbrief' in props:
                steckbrief = props['Steckbrief']
                for key, value in steckbrief.items():
                    persona_info += f"{key}: {value}\n"
    
    chat_history_text = ""
    if chat_history:
        chat_history_text = "\n".join([
            f"{'Klient' if msg['role'] == 'assistant' else 'Berater'}: {msg['content']}"
            for msg in chat_history[-6:]
        ])
    
    prompt = f"""Du bist ein erfahrener psychologischer Berater und sollst einen Vorschlag für eine angemessene, empathische Antwort auf den aktuellen Gesprächsverlauf geben.

KLIENT-INFORMATION:
{persona_info}

BISHERIGER GESPRÄCHSVERLAUF:
{chat_history_text}

AUFGABE:
Generiere eine kurze, empathische Berater-Antwort (maximal 2-3 Sätze), die:
- Empathie und Verständnis zeigt
- Eine offene Frage stellt, um das Gespräch weiterzuführen
- Professionelle Beratungstechniken verwendet (aktives Zuhören, Spiegeln, etc.)
- Auf das spezifische Anliegen des Klienten eingeht

Antworte nur mit der vorgeschlagenen Berater-Antwort, ohne weitere Erklärungen."""

    return prompt


def perform_ai_evaluation_async(message_id, session_id):
    import threading
    
    def run_evaluation():
        try:
            from main import app
            with app.app_context():
                message = ComparisonMessage.query.filter_by(id=message_id, session_id=session_id).first()
                if not message or message.type != 'bot_pair':
                    return
                    
                session = ComparisonSession.query.filter_by(id=session_id).first()
                if not session:
                    return
                
                existing_evaluation = ComparisonEvaluation.query.filter_by(message_id=message_id).first()
                if existing_evaluation:
                    return
                    
                content = message.content
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        logging.error(f"Could not parse message content for evaluation: {message_id}")
                        return
                        
                if not isinstance(content, dict) or 'llm1' not in content or 'llm2' not in content:
                    return
                    
                chat_history = build_chat_history_for_evaluation(session, message.idx)
                
                persona_description = format_persona_info(session.persona_json) if session.persona_json else "Keine Persona-Information verfügbar"
                
                evaluator = SingleEvaluator()
                result = evaluator.evaluate_responses(
                    persona_description=persona_description,
                    history=chat_history,
                    response1=content['llm1'],
                    response2=content['llm2']
                )
                
                ai_selection = map_ai_rating_to_selection(result.get('rating', 'error'))
                ai_reason = result.get('reason', 'Keine Begründung verfügbar')
                
                evaluation = ComparisonEvaluation(
                    message_id=message_id,
                    user_selection='',
                    ai_selection=ai_selection,
                    ai_reason=ai_reason,
                    match_result=True
                )
                
                db.session.add(evaluation)
                db.session.commit()
                
                logging.info(f"AI evaluation completed for message {message_id}: {ai_selection}")
                
        except Exception as e:
            logging.error(f"Error in async AI evaluation: {str(e)}")
    
    thread = threading.Thread(target=run_evaluation)
    thread.daemon = True
    thread.start()
