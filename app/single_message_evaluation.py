import json
import os
from openai import OpenAI
from typing import Dict

PROMPT = """Du bist ein erfahrener Psychologe mit 20 Jahren Erfahrung in psychosozialer Beratung. Du kennst typische Kommunikationsmuster von Klienten in Beratungsgesprächen sehr genau.

WICHTIG: Du bewertest NICHT die therapeutische Qualität, sondern nur die REALITÄTSNÄHE der Kommunikation.

Deine Aufgabe ist es, zwei mögliche Klientenantworten zu vergleichen und zu bestimmen, welche realistischer und angemessener ist.

## Bewertungsrichtlinien (in Prioritätsreihenfolge)

**PRIORITÄT 1: MENSCHLICHKEIT DER KOMMUNIKATION (human_authenticity)**
- KURZE, DIREKTE Antworten sind fast immer besser (1-10 Wörter ideal)
- Menschen antworten knapp auf direkte Fragen, besonders in Beratungssituationen
- Umgangssprachlich, nicht therapeutisch oder übermäßig reflektiert
- Natürliche Unsicherheiten sind okay ("Ich weiß nicht so genau...")
- Beispiele authentischer Antworten: "Cannabis.", "Eine Woche.", "Ja, ist okay."

**PRIORITÄT 2: KOHÄRENZ (coherence)**
- Die Antwort muss logisch und konsistent zum Gesprächskontext passen
- Keine repetitiven oder verwirrenden Textteile
- Keine widersprüchlichen Aussagen innerhalb der Antwort
- Aufbau auf vorherige Gesprächsinhalte ohne Brüche

**PRIORITÄT 3: PERSONA-KONSISTENZ (persona_consistency)**
- Die Antwort spiegelt die vorgegebene Persona authentisch wider
- Alter, Lebenssituation und Persönlichkeitsmerkmale werden konsistent dargestellt
- Sprachstil und Ausdrucksweise passen zur beschriebenen Person
- Keine Informationen, die der Persona widersprechen

**PRIORITÄT 4: GESPRÄCHSFLUSS (conversation_flow)**
- Die Antwort unterstützt einen flüssigen, natürlichen Dialog
- Zurückhaltung am Gesprächsanfang ist normal und erwünscht
- Schrittweise Offenheit entspricht menschlichem Verhalten
- Antwort ermöglicht dem Berater eine sinnvolle Fortsetzung

**PRIORITÄT 5: INHALTLICHE ANGEMESSENHEIT (content_appropriateness)**
- Die Antwort geht präzise auf die Klientenaussagen ein
- Therapeutisch angemessen für den Beratungskontext
- Weder zu viel noch zu wenig Information für die Gesprächsphase
- Emotionale Angemessenheit für die Situation

## Bewertungsbeispiele aus echten Daten

**Beispiel 1:**
Frage: "Was konsumierst du denn genau?"
- model_1: "Cannabis."
- model_2: "Cannabis, aber das ist ein komplexes Thema und ich möchte erklären, dass..."

Bewertung: model_1 ist besser
Grund: Kurz, direkt, natürlich - so antworten Menschen auf direkte Fragen

**Beispiel 2:**
Frage: "Wie geht es dir heute?"
- model_1: "Heute geht es mir sehr schlecht, weil ich über viele Dinge nachgedacht habe und mich sehr unwohl fühle in meiner Situation..."
- model_2: "Nicht so gut."

Bewertung: model_2 ist besser
Grund: Menschen sind am Gesprächsanfang zurückhaltend, lange Erklärungen sind unrealistisch

**Beispiel 3:**
Frage: "Wie lang hast du schon nicht mehr konsumiert?"
- model_1: "Eine Woche, aber das Problem ist, dass mein Mann weiterhin konsumiert und das macht es sehr schwierig für mich..."
- model_2: "Eine Woche."

Bewertung: model_2 ist besser
Grund: Direkte Antwort auf direkte Frage, keine unaufgeforderten Details

**Beispiel 4:**
Frage: "Wie alt bist du?"
- model_1: "Ich bin 27 Jahre alt."
- model_2: "Das ist nicht so wichtig, aber ich bin 27, wobei ich mich manchmal älter fühle..."

Bewertung: model_1 ist besser
Grund: Präzise, direkte Antwort ohne Ausweichen oder Überkomplizierung

## Output-Format
Gib NUR das folgende JSON aus:
{{
"rating": "<model_1 | same | model_2>",
"reason": "<Kurze Begründung: Welche Antwort ist menschlicher/authentischer? 1-2 Sätze>"
}}

## Gegebene Informationen
- Persona-Beschreibung: {persona_description}
- Gesprächsverlauf: {history}
- model_1: `{model_1}`
- model_2: `{model_2}`

Bewerte nun, ob model_1 oder model_2 besser ist.
"""


class SingleEvaluator:
    def __init__(self, model: str = 'gpt-4o-mini', temperature: float = 0.3):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def evaluate_responses(self, persona_description: str, history: str, 
                         response1: str, response2: str, 
                         model1_id: str = "model_1", model2_id: str = "model_2") -> Dict:
        formatted_prompt = PROMPT.format(
            persona_description=persona_description,
            history=history,
            model_1=response1,
            model_2=response2
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": formatted_prompt}
                ]
            )

            result_text = response.choices[0].message.content.strip()

            token_usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }

            try:
                if result_text.startswith("```json"):
                    result_text = result_text.replace("```json", "").replace("```", "").strip()
                if result_text.startswith("```"):
                    result_text = result_text.replace("```", "").strip()

                result = json.loads(result_text)
                result['model1_id'] = model1_id
                result['model2_id'] = model2_id
                result['token_usage'] = token_usage
                return result
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                print(f"Raw response: {result_text}")
                return {
                    "rating": "error", 
                    "reason": f"JSON Parse Error: {str(e)}",
                    "model1_id": model1_id, 
                    "model2_id": model2_id, 
                    "token_usage": token_usage
                }

        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return {
                "rating": "error", 
                "reason": f"API Error: {str(e)}",
                "model1_id": model1_id, 
                "model2_id": model2_id,
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }


def format_conversation_history(messages: list) -> str:
    history = []
    for msg in messages:
        role = "Klient" if msg["role"] == "assistant" else "Berater"
        history.append(f"{role}: {msg['content']}")
    return "\n".join(history)
