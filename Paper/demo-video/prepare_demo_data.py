#!/usr/bin/env python3
"""
Lars Demo Video - Daten-Vorbereitung
=====================================

Erstellt die benötigten Demo-Daten in der Datenbank:
1. Fertige Batch Generation mit 2 Modellen
2. Fertiges Evaluation Szenario mit Bewertungen

Nutzung:
    python prepare_demo_data.py          # Erstellt alles
    python prepare_demo_data.py --clean  # Löscht Demo-Daten
    python prepare_demo_data.py --check  # Prüft ob Daten existieren

Voraussetzung: Lars muss laufen (docker compose up)
"""

import requests
import json
import time
import argparse
from pathlib import Path

# Konfiguration
BASE_URL = "http://localhost:55080/api"
AUTH_URL = "http://localhost:55080/auth"

# Demo-Daten Bezeichner
DEMO_PREFIX = "IJCAI Demo"
PROMPT_NAME = f"{DEMO_PREFIX} - News Summary"
BATCH_JOB_NAME = f"{DEMO_PREFIX} - Batch Generation"
SCENARIO_NAME = f"{DEMO_PREFIX} - Evaluation"

# News Artikel für Demo
NEWS_ARTICLES = [
    {
        "id": "news_001",
        "title": "Breakthrough in Quantum Computing",
        "content": "Scientists at MIT announced a major breakthrough in quantum computing yesterday. The team successfully demonstrated a 1000-qubit processor that maintains coherence for over 10 minutes, a significant improvement over previous records."
    },
    {
        "id": "news_002",
        "title": "Global Climate Summit Reaches Historic Agreement",
        "content": "World leaders at the 2026 Global Climate Summit in Berlin have agreed to reduce carbon emissions by 60% by 2035. The agreement includes binding commitments and financial penalties for non-compliance."
    },
    {
        "id": "news_003",
        "title": "AI System Passes Medical Licensing Exam",
        "content": "An artificial intelligence system developed by Stanford researchers has passed the US Medical Licensing Examination with a score in the 90th percentile. The system demonstrated diagnostic accuracy comparable to experienced physicians."
    }
]


class DemoDataPreparer:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None

    def login(self, username="admin", password="admin123"):
        """Login und Token holen"""
        print(f"🔐 Login als {username}...")

        # Lars verwendet Authentik OAuth, aber wir können direkt die Session nutzen
        # Für API-Zugriff brauchen wir einen gültigen Token

        # Versuche direkt die API zu nutzen (wenn bereits eingeloggt)
        try:
            resp = self.session.get(f"{BASE_URL}/auth/me", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.user_id = data.get('id')
                print(f"   ✓ Bereits eingeloggt als {data.get('username')}")
                return True
        except:
            pass

        print("   ⚠️ API-Zugriff benötigt gültigen Login")
        print("   Bitte im Browser einloggen: http://localhost:55080")
        return False

    def check_api(self):
        """Prüft ob die API erreichbar ist"""
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=5)
            return resp.status_code == 200
        except:
            return False

    def create_prompt(self):
        """Erstellt den Demo-Prompt"""
        print(f"\n📝 Erstelle Prompt: {PROMPT_NAME}")

        prompt_data = {
            "name": PROMPT_NAME,
            "description": "Demo prompt for IJCAI video - News article summarization",
            "blocks": [
                {
                    "name": "System",
                    "content": "You are an expert news editor creating concise summaries.\n\nRequirements:\n- Exactly 2 sentences\n- Factually accurate\n- Neutral journalistic tone",
                    "role": "system"
                },
                {
                    "name": "User",
                    "content": "Please summarize this news article:\n\nTitle: {{title}}\n\nContent: {{content}}",
                    "role": "user"
                }
            ]
        }

        try:
            resp = self.session.post(
                f"{BASE_URL}/prompts",
                json=prompt_data,
                timeout=10
            )
            if resp.status_code in [200, 201]:
                data = resp.json()
                print(f"   ✓ Prompt erstellt (ID: {data.get('id')})")
                return data.get('id')
            elif resp.status_code == 409:
                print(f"   ♻️ Prompt existiert bereits")
                # Hole existierenden Prompt
                resp = self.session.get(f"{BASE_URL}/prompts", timeout=10)
                prompts = resp.json()
                for p in prompts:
                    if p.get('name') == PROMPT_NAME:
                        return p.get('id')
            else:
                print(f"   ⚠️ Fehler: {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            print(f"   ⚠️ Fehler: {e}")

        return None

    def create_batch_job(self, prompt_id):
        """Erstellt einen Batch Generation Job"""
        print(f"\n🔄 Erstelle Batch Job: {BATCH_JOB_NAME}")

        job_data = {
            "name": BATCH_JOB_NAME,
            "prompt_id": prompt_id,
            "models": ["gpt-4", "mistral-7b"],  # Zwei Modelle für Vergleich
            "data": NEWS_ARTICLES,
            "config": {
                "temperature": 0.7,
                "max_tokens": 200
            }
        }

        try:
            resp = self.session.post(
                f"{BASE_URL}/generation/jobs",
                json=job_data,
                timeout=30
            )
            if resp.status_code in [200, 201]:
                data = resp.json()
                job_id = data.get('id')
                print(f"   ✓ Job erstellt (ID: {job_id})")

                # Job starten
                print(f"   🚀 Starte Job...")
                self.session.post(f"{BASE_URL}/generation/jobs/{job_id}/start")

                return job_id
            else:
                print(f"   ⚠️ Fehler: {resp.status_code}")
        except Exception as e:
            print(f"   ⚠️ Fehler: {e}")

        return None

    def create_scenario(self, job_id=None):
        """Erstellt ein Evaluation Szenario"""
        print(f"\n📊 Erstelle Szenario: {SCENARIO_NAME}")

        scenario_data = {
            "name": SCENARIO_NAME,
            "description": "Demo evaluation scenario for IJCAI video",
            "type": "ranking",
            "config": {
                "buckets": 3,
                "labels": ["Best", "Acceptable", "Poor"]
            }
        }

        if job_id:
            scenario_data["source_job_id"] = job_id

        try:
            resp = self.session.post(
                f"{BASE_URL}/scenarios",
                json=scenario_data,
                timeout=10
            )
            if resp.status_code in [200, 201]:
                data = resp.json()
                print(f"   ✓ Szenario erstellt (ID: {data.get('id')})")
                return data.get('id')
            else:
                print(f"   ⚠️ Fehler: {resp.status_code}")
        except Exception as e:
            print(f"   ⚠️ Fehler: {e}")

        return None

    def cleanup(self):
        """Löscht alle Demo-Daten"""
        print("\n🧹 Lösche Demo-Daten...")

        # Via Docker/MariaDB
        import subprocess
        cleanup_sql = f"""
        DELETE FROM user_prompts WHERE name LIKE '%{DEMO_PREFIX}%';
        DELETE FROM scenario_users WHERE scenario_id IN (SELECT id FROM scenarios WHERE name LIKE '%{DEMO_PREFIX}%');
        DELETE FROM scenarios WHERE name LIKE '%{DEMO_PREFIX}%';
        DELETE FROM generation_outputs WHERE job_id IN (SELECT id FROM generation_jobs WHERE name LIKE '%{DEMO_PREFIX}%');
        DELETE FROM generation_jobs WHERE name LIKE '%{DEMO_PREFIX}%';
        """

        try:
            result = subprocess.run(
                ['docker', 'exec', 'llars_db_service', 'mariadb',
                 '-u', 'dev_user', '-pdev_password_change_me', 'database_llars',
                 '-e', cleanup_sql],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                print("   ✓ Demo-Daten gelöscht")
            else:
                print(f"   ⚠️ Fehler: {result.stderr}")
        except Exception as e:
            print(f"   ⚠️ Fehler: {e}")

    def check_data(self):
        """Prüft ob Demo-Daten existieren"""
        print("\n🔍 Prüfe Demo-Daten...")

        checks = {
            "API erreichbar": self.check_api(),
            "Prompt": False,
            "Batch Job": False,
            "Szenario": False
        }

        if checks["API erreichbar"]:
            try:
                # Prüfe Prompts
                resp = self.session.get(f"{BASE_URL}/prompts", timeout=10)
                if resp.status_code == 200:
                    prompts = resp.json()
                    checks["Prompt"] = any(p.get('name') == PROMPT_NAME for p in prompts)

                # Prüfe Jobs
                resp = self.session.get(f"{BASE_URL}/generation/jobs", timeout=10)
                if resp.status_code == 200:
                    jobs = resp.json()
                    checks["Batch Job"] = any(j.get('name') == BATCH_JOB_NAME for j in jobs)

                # Prüfe Szenarien
                resp = self.session.get(f"{BASE_URL}/scenarios", timeout=10)
                if resp.status_code == 200:
                    scenarios = resp.json()
                    checks["Szenario"] = any(s.get('name') == SCENARIO_NAME for s in scenarios)
            except Exception as e:
                print(f"   ⚠️ API-Fehler: {e}")

        print("\n   Status:")
        for name, ok in checks.items():
            status = "✓" if ok else "✗"
            print(f"   {status} {name}")

        return all(checks.values())


def main():
    parser = argparse.ArgumentParser(description="Lars Demo-Daten vorbereiten")
    parser.add_argument('--clean', action='store_true', help='Demo-Daten löschen')
    parser.add_argument('--check', action='store_true', help='Demo-Daten prüfen')
    args = parser.parse_args()

    preparer = DemoDataPreparer()

    if args.clean:
        preparer.cleanup()
    elif args.check:
        preparer.check_data()
    else:
        print("="*60)
        print("Lars Demo-Daten Vorbereitung")
        print("="*60)

        if not preparer.check_api():
            print("\n❌ Lars API nicht erreichbar!")
            print("   Starte Lars mit: ./start_llars.sh")
            return

        # Login
        if not preparer.login():
            print("\n⚠️ Manueller Schritt erforderlich:")
            print("   1. Öffne http://localhost:55080 im Browser")
            print("   2. Logge dich als admin ein")
            print("   3. Führe dieses Skript erneut aus")
            return

        # Prompt erstellen
        prompt_id = preparer.create_prompt()

        # Batch Job erstellen (wenn API-Zugriff funktioniert)
        if prompt_id:
            job_id = preparer.create_batch_job(prompt_id)

            # Szenario erstellen
            if job_id:
                preparer.create_scenario(job_id)

        print("\n" + "="*60)
        print("✓ Demo-Daten vorbereitet!")
        print("="*60)
        print("\nNächste Schritte:")
        print("   1. python run.py --test  # Elemente prüfen")
        print("   2. python run.py --audio # Audio generieren")
        print("   3. python run.py         # Video aufnehmen")


if __name__ == '__main__':
    main()
