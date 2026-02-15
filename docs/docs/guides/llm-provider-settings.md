# LLM Provider (Einstellungen)

**Version:** 1.0 | **Stand:** Februar 2026

Unter **Settings → LLM-Provider** können alle Nutzer eigene LLM-API-Keys hinterlegen, testen und mit anderen Nutzern oder Rollen teilen. Die hier konfigurierten Provider stehen anschließend systemweit in der Modellauswahl (`LlmModelSelect`) zur Verfügung.

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Settings → LLM-Provider                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Meine Provider                                  [+ Hinzufügen]│   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │  🤖 OpenAI             GPT-5, GPT-5-mini   ✓  ⋮ (Menü)       │   │
│  │  🧠 Anthropic          api.anthropic.com    ✓  ⋮ (Menü)       │   │
│  │  ⚡ LiteLLM            litellm.example.com  ✓  ⋮ (Menü)       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Shared With Me                                                 │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │  🖥 Ollama  (von admin)       llama3, mistral                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

Die Seite gliedert sich in zwei Bereiche:

- **Meine Provider** — Selbst angelegte Provider mit API-Key, Test- und Share-Funktionen
- **Shared With Me** — Von anderen Nutzern freigegebene Provider (nur lesen)

---

## Schnellstart

!!! tip "In 5 Schritten zum ersten Provider"
    1. **Settings** öffnen (Zahnrad-Icon in der oberen Leiste)
    2. Tab **LLM-Provider** auswählen
    3. **+ Hinzufügen** klicken
    4. Provider-Typ wählen, API-Key eingeben, Modelle auswählen
    5. **Erstellen** → fertig! Der Provider erscheint in der Modellauswahl.

---

## Provider-Typen

| Typ | Beschreibung | API-Key | Base-URL | Besonderheiten |
|-----|-------------|---------|----------|----------------|
| **OpenAI** | GPT-5, GPT-4.1, o3/o4 | Ja | Optional | Modellauswahl per Dropdown |
| **Anthropic** | Claude Modelle | Ja | Optional | — |
| **Google Gemini** | Gemini Pro, Ultra | Ja | Nein | — |
| **Azure OpenAI** | Azure-gehostete OpenAI | Ja | Ja | Deployment Name erforderlich |
| **Ollama** | Lokale Installation | Nein | Ja | Standard: `http://localhost:11434` |
| **LiteLLM** | Multi-Provider Proxy | Ja | Ja | — |
| **Custom** | OpenAI-kompatibler Endpunkt | Ja | Ja | Für beliebige OpenAI-kompatible APIs |

!!! info "Welchen Typ wählen?"
    - **Eigener OpenAI-Account** → Typ `OpenAI`
    - **Eigener Anthropic-Account** → Typ `Anthropic`
    - **Lokales Modell (Ollama, vLLM)** → Typ `Ollama` oder `Custom`
    - **Uni/Firmen-Proxy** → Typ `LiteLLM` oder `Custom`

---

## Provider hinzufügen

Klicken Sie auf **+ Hinzufügen**, um den Dialog zu öffnen:

```
┌─────────────────────────────────────────────────────┐
│  Provider hinzufügen                                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Typ:        [OpenAI              ▾]                │
│                                                     │
│  API-Key:    [sk-...                  👁]           │
│                                                     │
│  Modelle:    [GPT-5] [GPT-5 Mini] [GPT-4.1]  ×    │
│              Modelle auswählen die verfügbar         │
│              sein sollen                             │
│                                                     │
│  ☐ Als Standard setzen                              │
│                                                     │
│                        [Abbrechen]  [Erstellen]     │
└─────────────────────────────────────────────────────┘
```

### Felder im Detail

| Feld | Beschreibung |
|------|-------------|
| **Typ** | Provider-Art (OpenAI, Anthropic, etc.) — nach Erstellung nicht änderbar |
| **Name** | Anzeigename (bei OpenAI automatisch gesetzt) |
| **API-Key** | API-Schlüssel des Providers — wird verschlüsselt gespeichert |
| **Modelle** | Nur bei OpenAI: Dropdown mit verfügbaren Modellen (Mehrfachauswahl) |
| **Base-URL** | Nur bei Providern mit eigener URL (Ollama, LiteLLM, Custom, etc.) |
| **Als Standard** | Dieser Provider wird bevorzugt verwendet |

!!! warning "API-Key Sicherheit"
    Der API-Key wird serverseitig verschlüsselt gespeichert. Er ist nach dem Speichern nicht mehr im Klartext abrufbar. Beim Bearbeiten kann er leer gelassen werden, um den vorhandenen Key beizubehalten.

### OpenAI: Modellauswahl

Bei OpenAI können Sie gezielt die Modelle auswählen, die verfügbar sein sollen:

| Modell | Kontext | Output | Vision | Reasoning |
|--------|---------|--------|--------|-----------|
| GPT-5.2 | 400K | 128K | Ja | Ja |
| GPT-5.1 | 400K | 128K | Ja | Ja |
| GPT-5 | 400K | 128K | Ja | Ja |
| GPT-5 Mini | 400K | 128K | Ja | Nein |
| GPT-5 Nano | 400K | 128K | Nein | Nein |
| GPT-4.1 | 1M | 32K | Ja | Nein |
| GPT-4.1 Mini | 1M | 32K | Ja | Nein |
| GPT-4.1 Nano | 1M | 32K | Ja | Nein |
| GPT-4o | 128K | 16K | Ja | Nein |
| o3 | 200K | 100K | Ja | Ja |
| o4 Mini | 200K | 100K | Ja | Ja |

---

## Verbindung testen

So prüfen Sie, ob Ihr API-Key gültig ist:

1. Klicken Sie auf das **⋮-Menü** des Providers
2. Wählen Sie **Verbindung testen**
3. LLARS sendet eine Test-Anfrage an den Provider
4. Ergebnis: Erfolgsmeldung oder Fehlerbeschreibung

!!! tip "Test schlägt fehl?"
    - **401/403** → API-Key ungültig oder abgelaufen
    - **Timeout** → Base-URL nicht erreichbar (Firewall, VPN?)
    - **Modell nicht gefunden** → Prüfen Sie die ausgewählten Modelle

---

## Provider teilen

Eigene Provider können mit einzelnen Nutzern, ganzen Rollen oder allen Nutzern geteilt werden.

### Share-Dialog öffnen

1. **⋮-Menü** → **Teilen** klicken
2. Der Share-Dialog erscheint:

```
┌─────────────────────────────────────────────────────┐
│  "OpenAI" teilen                                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Aktuelle Freigaben:                                │
│  [👤 evaluator ×] [👥 researcher ×]                │
│                                                     │
│  ☐ Mit allen Nutzern teilen                         │
│  ─────────────────────────────────                  │
│  Freigabe hinzufügen:                               │
│  [Nutzer | Rolle]                                   │
│                                                     │
│  [Nutzer suchen...              ] [Teilen]          │
│                                                     │
│                                         [Schließen] │
└─────────────────────────────────────────────────────┘
```

### Sharing-Optionen

| Option | Beschreibung |
|--------|-------------|
| **Mit Nutzer teilen** | Autocomplete-Suche nach Benutzername → Einzelfreigabe |
| **Mit Rolle teilen** | Rollenname eingeben (z.B. `researcher`) → alle Nutzer dieser Rolle |
| **Mit allen teilen** | Toggle-Schalter → Provider ist für alle sichtbar |

### Freigabe entfernen

Klicken Sie auf das **×** an einem Freigabe-Chip, um die Freigabe zu widerrufen.

!!! info "Was können Empfänger?"
    Empfänger können den geteilten Provider **nur nutzen** (Modelle auswählen), aber **nicht** bearbeiten, löschen oder weiter teilen. Der API-Key bleibt unsichtbar.

---

## Geteilte Provider nutzen

Provider, die andere Nutzer mit Ihnen geteilt haben, erscheinen im Bereich **Shared With Me**:

- Angezeigt wird: Provider-Name, Typ, verfügbare Modelle und **wer** geteilt hat
- Die Modelle erscheinen automatisch in der **Modellauswahl** (`LlmModelSelect`) in allen Bereichen (Generation, Prompt Engineering, Chatbot, etc.)
- Das Modell-ID-Format für geteilte Provider: `user-provider:{id}:{username}:{model}`

---

## Provider verwalten

Über das **⋮-Menü** eines Providers stehen folgende Aktionen bereit:

| Aktion | Beschreibung |
|--------|-------------|
| **Verbindung testen** | Test-Anfrage an den Provider senden |
| **Bearbeiten** | Name, API-Key, Base-URL oder Modelle ändern |
| **Teilen** | Share-Dialog öffnen |
| **Als Standard** | Provider als bevorzugten Default setzen |
| **Löschen** | Provider unwiderruflich entfernen (inkl. aller Freigaben) |

### Nutzungsstatistiken

Für jeden Provider werden folgende Informationen angezeigt:

- **Anfragen** — Gesamtzahl der API-Aufrufe
- **Zuletzt verwendet** — Datum der letzten Nutzung
- **API-Key Status** — Grünes Häkchen (gesetzt) oder Warnung (fehlt)

---

## API-Endpunkte

| Methode | Endpunkt | Beschreibung |
|---------|----------|-------------|
| GET | `/api/user/providers` | Eigene Provider auflisten |
| GET | `/api/user/providers/available` | Eigene + geteilte Provider |
| GET | `/api/user/providers/types` | Verfügbare Provider-Typen |
| POST | `/api/user/providers` | Provider erstellen |
| GET | `/api/user/providers/<id>` | Provider-Details |
| PUT | `/api/user/providers/<id>` | Provider aktualisieren |
| DELETE | `/api/user/providers/<id>` | Provider löschen |
| POST | `/api/user/providers/<id>/test` | Verbindung testen |
| POST | `/api/user/providers/models` | Modelle eines Providers abrufen |
| GET | `/api/user/providers/<id>/shares` | Freigaben auflisten |
| POST | `/api/user/providers/<id>/shares` | Freigabe erstellen |
| DELETE | `/api/user/providers/<id>/shares/<share_id>` | Freigabe entfernen |
| POST | `/api/user/providers/<id>/share-all` | Mit allen teilen (Toggle) |

---

## Berechtigungen

Jeder authentifizierte Nutzer kann eigene Provider anlegen — es wird keine spezielle Berechtigung benötigt.

| Aktion | Voraussetzung |
|--------|--------------|
| Provider anlegen/bearbeiten/löschen | Eingeloggt (beliebige Rolle) |
| Provider testen | Eingeloggt (beliebige Rolle) |
| Provider teilen | Eingeloggt (eigener Provider) |
| Alle Provider sehen (Admin) | `admin:system:configure` |

---

## Siehe auch

- [Admin Dashboard](admin-dashboard.md) — LLM-Provider und Modelle zentral verwalten (Admin)
- [Batch Generation](batch-generation.md) — Modelle für Massenverarbeitung auswählen
- [Prompt Engineering](prompt-engineering.md) — Prompts mit verschiedenen Modellen testen
- [Berechtigungssystem](permission-system.md) — Rollen und Rechte
