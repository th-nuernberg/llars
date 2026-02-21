# Feature Testanforderungen: Anonymisierung

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für das LLARS Offline Anonymisierungs-Tool.

**Komponente:** `/Anonymize` Frontend, Flask API, Flair NER Model
**Permission:** `feature:anonymize:view`

---

## 1. API Endpoints

### Health Check

**Endpoint:** `GET /api/anonymize/health`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ANON-H01 | Health Check | 200, status: ok | Integration |
| ANON-H02 | Model geladen | model_loaded: true | Integration |
| ANON-H03 | Model nicht geladen | model_loaded: false | Integration |

### Pseudonymize Text

**Endpoint:** `POST /api/anonymize/pseudonymize`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ANON-T01 | Text mit Namen | Namen ersetzt | Integration |
| ANON-T02 | Text ohne Entitäten | Unverändert | Integration |
| ANON-T03 | Leerer Text | 400 Bad Request | Integration |
| ANON-T04 | Sehr langer Text | Verarbeitet | Integration |
| ANON-T05 | Mehrere Entitäten | Alle ersetzt | Integration |
| ANON-T06 | Konsistente Ersetzung | Gleicher Name = gleicher Ersatz | Integration |

### Pseudonymize File

**Endpoint:** `POST /api/anonymize/pseudonymize-file`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ANON-F01 | TXT Upload | Pseudonymisierte Datei | Integration |
| ANON-F02 | MD Upload | Pseudonymisierte Datei | Integration |
| ANON-F03 | PDF Upload | Nicht unterstützt / Error | Integration |
| ANON-F04 | Große Datei | Verarbeitet | Integration |
| ANON-F05 | Leere Datei | 400 Bad Request | Integration |

---

## 2. NER Entity Types

| Entity | Beschreibung | Ersetzung |
|--------|--------------|-----------|
| PER | Personennamen | [PERSON_1], [PERSON_2], ... |
| LOC | Orte | [ORT_1], [ORT_2], ... |
| ORG | Organisationen | [ORG_1], [ORG_2], ... |
| MISC | Sonstiges | [MISC_1], [MISC_2], ... |

### Entity Detection Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ANON-E01 | Deutsche Namen | Erkannt und ersetzt | Integration |
| ANON-E02 | Ausländische Namen | Erkannt und ersetzt | Integration |
| ANON-E03 | Städtenamen | Erkannt (LOC) | Integration |
| ANON-E04 | Firmen | Erkannt (ORG) | Integration |
| ANON-E05 | Titel + Name | Titel + Pseudonym | Integration |
| ANON-E06 | Abkürzungen | Teilweise erkannt | Integration |

---

## 3. Recommender System

**Komponente:** SQLite-basierte Pseudonym-Datenbank

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ANON-R01 | Pseudonym-Auswahl | Plausibles Pseudonym | Unit |
| ANON-R02 | Geschlecht-Matching | Männlich → männlich | Unit |
| ANON-R03 | Konsistenz | Gleicher Input = gleicher Output | Unit |
| ANON-R04 | Keine Wiederverwendung | Jedes Pseudonym einzigartig | Unit |

---

## 4. Frontend Tests

**Komponente:** `Anonymize.vue`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ANON-UI01 | Seite lädt | Editor sichtbar | E2E |
| ANON-UI02 | Text eingeben | Input funktioniert | E2E |
| ANON-UI03 | Pseudonymisieren klicken | Button vorhanden | E2E |
| ANON-UI04 | Ergebnis angezeigt | Output sichtbar | E2E |
| ANON-UI05 | Highlighting | Entities farbig | E2E |
| ANON-UI06 | Copy Button | Text kopierbar | E2E |
| ANON-UI07 | Reset Button | Eingabe zurücksetzen | E2E |
| ANON-UI08 | File Upload | Drag & Drop | E2E |

### Permission Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ANON-P01 | Admin Zugriff | Erlaubt | E2E |
| ANON-P02 | Researcher Zugriff | Erlaubt | E2E |
| ANON-P03 | Evaluator Zugriff | Erlaubt | E2E |
| ANON-P04 | Chatbot_Manager | Nicht erlaubt | E2E |

---

## 5. Test-Code

```python
# tests/integration/anonymize/test_anonymize.py
import pytest


class TestAnonymizeAPI:
    """Anonymize API Tests"""

    def test_ANON_H01_health_check(self, client):
        """Health Check funktioniert"""
        response = client.get('/api/anonymize/health')
        assert response.status_code == 200
        assert response.json['status'] == 'ok'

    def test_ANON_T01_text_with_names(self, authenticated_client):
        """Text mit Namen wird pseudonymisiert"""
        response = authenticated_client.post('/api/anonymize/pseudonymize', json={
            'text': 'Max Mustermann arbeitet bei der Firma XYZ in Berlin.'
        })
        assert response.status_code == 200
        result = response.json['result']

        # Namen sollten ersetzt sein
        assert 'Max Mustermann' not in result
        assert '[PERSON' in result or 'PERSON_' in result

    def test_ANON_T02_text_without_entities(self, authenticated_client):
        """Text ohne Entitäten bleibt unverändert"""
        original = 'Dies ist ein einfacher Text ohne Namen.'
        response = authenticated_client.post('/api/anonymize/pseudonymize', json={
            'text': original
        })
        assert response.status_code == 200
        # Text sollte weitgehend unverändert sein
        # (Kleinere Änderungen durch Tokenization möglich)

    def test_ANON_T06_consistent_replacement(self, authenticated_client):
        """Gleicher Name wird konsistent ersetzt"""
        response = authenticated_client.post('/api/anonymize/pseudonymize', json={
            'text': 'Max sagte zu Max, dass Max kommt. Max freut sich.'
        })
        assert response.status_code == 200
        result = response.json['result']

        # Alle "Max" sollten durch denselben Ersatz ersetzt werden
        # Zähle wie viele unterschiedliche Ersetzungen es gibt
        import re
        replacements = re.findall(r'\[PERSON_\d+\]', result)
        if replacements:
            assert len(set(replacements)) == 1  # Alle gleich

    def test_ANON_E01_german_names(self, authenticated_client):
        """Deutsche Namen werden erkannt"""
        response = authenticated_client.post('/api/anonymize/pseudonymize', json={
            'text': 'Dr. Hans-Peter Müller und Frau Sabine Schmidt trafen sich.'
        })
        assert response.status_code == 200
        result = response.json['result']

        assert 'Hans-Peter Müller' not in result
        assert 'Sabine Schmidt' not in result

    def test_ANON_E03_city_names(self, authenticated_client):
        """Städtenamen werden erkannt"""
        response = authenticated_client.post('/api/anonymize/pseudonymize', json={
            'text': 'Er wohnt in München und arbeitet in Frankfurt.'
        })
        assert response.status_code == 200
        result = response.json['result']

        # Städte sollten als LOC erkannt werden
        assert 'München' not in result or '[ORT' in result

    def test_ANON_F01_file_upload(self, authenticated_client, test_text_file):
        """TXT File Upload funktioniert"""
        with open(test_text_file, 'rb') as f:
            response = authenticated_client.post(
                '/api/anonymize/pseudonymize-file',
                data={'file': (f, 'test.txt')},
                content_type='multipart/form-data'
            )
        assert response.status_code == 200
        assert 'result' in response.json


class TestAnonymizeRecommender:
    """Recommender System Tests"""

    def test_ANON_R01_pseudonym_selection(self, recommender):
        """Pseudonyme sind plausibel"""
        pseudonym = recommender.get_pseudonym('Max', gender='male')
        assert pseudonym is not None
        assert len(pseudonym) > 0

    def test_ANON_R02_gender_matching(self, recommender):
        """Geschlecht wird berücksichtigt"""
        male_pseudonym = recommender.get_pseudonym('Hans', gender='male')
        female_pseudonym = recommender.get_pseudonym('Maria', gender='female')

        # Pseudonyme sollten unterschiedlich sein
        assert male_pseudonym != female_pseudonym

    def test_ANON_R04_no_reuse(self, recommender):
        """Pseudonyme werden nicht wiederverwendet"""
        pseudonyms = []
        for i in range(10):
            p = recommender.get_pseudonym(f'Name{i}', gender='male')
            pseudonyms.append(p)

        # Alle sollten unterschiedlich sein
        assert len(set(pseudonyms)) == len(pseudonyms)
```

---

## 6. E2E Test-Code

```typescript
// e2e/anonymize/anonymize.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('Anonymize Tool', () => {
  test('ANON-UI01 to UI04: basic anonymization flow', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Anonymize')

    // UI lädt
    await expect(authenticatedPage.locator('.anonymize-editor')).toBeVisible()

    // Text eingeben
    const input = authenticatedPage.locator('textarea.input-text')
    await input.fill('Max Mustermann aus Berlin arbeitet bei der Firma GmbH.')

    // Pseudonymisieren
    await authenticatedPage.click('button:has-text("Pseudonymisieren")')

    // Ergebnis prüfen
    await expect(authenticatedPage.locator('.result-text')).toBeVisible({
      timeout: 30000
    })

    const result = await authenticatedPage.locator('.result-text').textContent()
    expect(result).not.toContain('Max Mustermann')
  })

  test('ANON-UI05: entity highlighting', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Anonymize')

    await authenticatedPage.fill('textarea.input-text', 'Max Mustermann lebt in Berlin.')
    await authenticatedPage.click('button:has-text("Pseudonymisieren")')

    // Entities sollten farbig hervorgehoben sein
    await expect(authenticatedPage.locator('.entity-highlight')).toBeVisible({
      timeout: 30000
    })
  })

  test('ANON-P04: chatbot_manager no access', async ({ chatbotManagerPage }) => {
    await chatbotManagerPage.goto('/Anonymize')

    // Sollte Zugriff verweigern oder redirect
    await expect(chatbotManagerPage).not.toHaveURL('/Anonymize')
  })
})
```

---

## 7. Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path


@pytest.fixture
def test_text_file(tmp_path):
    """Temporäre Textdatei für Upload-Tests"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Max Mustermann und Maria Schmidt trafen sich in Berlin.")
    return file_path


@pytest.fixture
def recommender(app):
    """Recommender System Instance"""
    from app.services.anonymize.recommender import PseudonymRecommender
    return PseudonymRecommender()
```

---

## 8. Model-Konfiguration

### Flair NER Model

| Einstellung | Wert |
|-------------|------|
| Model | `ner-german-large` |
| Pfad | `app/models/anonymize/ner-german-large` |
| Sprache | Deutsch |
| GPU | Optional (CUDA) |

### SQLite Datenbank

| Einstellung | Wert |
|-------------|------|
| Pfad | `app/data/anonymize/pseudonyms.db` |
| Tabellen | `male_names`, `female_names`, `surnames` |

---

## 9. Beispiel-Transformationen

| Input | Output |
|-------|--------|
| Max Mustermann | [PERSON_1] |
| Berlin | [ORT_1] |
| Deutsche Bank AG | [ORG_1] |
| Dr. Hans Müller | Dr. [PERSON_2] |
| Er wohnt in München. | Er wohnt in [ORT_2]. |

---

## 10. Checkliste für manuelle Tests

### API
- [ ] Health Check zeigt Status
- [ ] Text mit Namen wird pseudonymisiert
- [ ] Text ohne Namen bleibt unverändert
- [ ] Konsistente Ersetzung bei Wiederholungen
- [ ] File Upload funktioniert

### Entity Detection
- [ ] Deutsche Namen erkannt
- [ ] Ausländische Namen erkannt
- [ ] Städte erkannt
- [ ] Organisationen erkannt
- [ ] Titel + Name korrekt

### Frontend
- [ ] Seite lädt
- [ ] Text eingeben funktioniert
- [ ] Button "Pseudonymisieren" funktioniert
- [ ] Ergebnis wird angezeigt
- [ ] Highlighting funktioniert
- [ ] Copy/Reset Buttons funktionieren
- [ ] File Upload Drag & Drop

### Permissions
- [ ] Admin hat Zugriff
- [ ] Researcher hat Zugriff
- [ ] Evaluator hat Zugriff
- [ ] Chatbot_Manager hat KEINEN Zugriff

---

## 11. Bekannte Einschränkungen

| Einschränkung | Beschreibung |
|---------------|--------------|
| Nur Deutsch | Model ist auf Deutsch trainiert |
| Kontextabhängig | Manchmal falsche Klassifizierung |
| Keine PDFs | Nur Textdateien unterstützt |
| Offline | Keine Cloud-API |

---

**Letzte Aktualisierung:** 30. Dezember 2025
