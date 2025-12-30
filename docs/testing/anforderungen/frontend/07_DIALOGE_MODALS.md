# Frontend Testanforderungen: Dialoge & Modals

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt Tests für ALLE Dialoge und Modals in LLARS.

**Anzahl:** 10 Dialog-Komponenten | 2 Verschachtelte Dialoge

---

## 1. UserSettingsDialog

**Datei:** `src/components/UserSettingsDialog.vue`
**Trigger:** AppBar → User-Menu → Einstellungen

### Öffnen/Schließen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| USD-O01 | Dialog öffnen | Dialog sichtbar | E2E |
| USD-O02 | X-Button klicken | Dialog schließt | E2E |
| USD-O03 | Außerhalb klicken | Dialog schließt | E2E |
| USD-O04 | Escape-Taste | Dialog schließt | E2E |

### Profil-Sektion

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| USD-P01 | Username angezeigt | Korrekter Name | E2E |
| USD-P02 | Email angezeigt | Korrekte Email | E2E |
| USD-P03 | Rolle angezeigt | Admin/User Badge | E2E |
| USD-P04 | Avatar angezeigt | Bild oder Placeholder | E2E |

### Theme-Einstellungen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| USD-T01 | System-Option | Chip anklickbar | E2E |
| USD-T02 | Light-Option | Chip anklickbar | E2E |
| USD-T03 | Dark-Option | Chip anklickbar | E2E |
| USD-T04 | Theme wechseln | Seite ändert Theme | E2E |

### Collab-Farbe

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| USD-C01 | Farben angezeigt | Alle Presets sichtbar | E2E |
| USD-C02 | Farbe auswählen | Auswahl markiert | E2E |
| USD-C03 | Farbe speichern | API-Call erfolgreich | E2E |
| USD-C04 | Farbe in Editor | Korrekte Farbe im Collab | E2E |

### Avatar-Management

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| USD-A01 | Upload Button | File-Dialog öffnet | E2E |
| USD-A02 | Bild hochladen | Avatar aktualisiert | E2E |
| USD-A03 | Neues Standardbild | Avatar regeneriert | E2E |
| USD-A04 | Zurücksetzen | Original-Avatar | E2E |
| USD-A05 | Rate Limit (3/Tag) | Warnung bei Überschreitung | E2E |
| USD-A06 | Zu große Datei | Fehlermeldung | E2E |
| USD-A07 | Falsches Format | Fehlermeldung | E2E |

---

## 2. DocumentUploadDialog

**Datei:** `src/components/RAG/DocumentUploadDialog.vue`
**Trigger:** RAG Admin → Dokumente → Upload

### Öffnen/Schließen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DUD-O01 | Dialog öffnen | Dialog sichtbar | E2E |
| DUD-O02 | Schließen während Upload | Warnung anzeigen | E2E |

### Drag & Drop

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DUD-DD01 | Datei reinziehen | Drop-Zone hervorgehoben | E2E |
| DUD-DD02 | Datei ablegen | Datei in Liste | E2E |
| DUD-DD03 | Mehrere Dateien | Alle in Liste | E2E |

### File Selection

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DUD-FS01 | Dateien auswählen Button | File-Dialog öffnet | E2E |
| DUD-FS02 | PDF auswählen | In Liste angezeigt | E2E |
| DUD-FS03 | TXT auswählen | In Liste angezeigt | E2E |
| DUD-FS04 | MD auswählen | In Liste angezeigt | E2E |
| DUD-FS05 | Ungültiger Typ (.exe) | Fehlermeldung | E2E |

### Collection

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DUD-COL01 | Dropdown öffnen | Collections angezeigt | E2E |
| DUD-COL02 | Collection wählen | Auswahl gesetzt | E2E |

### Upload-Prozess

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DUD-UP01 | Upload starten | Progress-Bar erscheint | E2E |
| DUD-UP02 | Pro-Datei Progress | Einzelne Fortschritte | E2E |
| DUD-UP03 | Upload erfolgreich | Success-Icon | E2E |
| DUD-UP04 | Upload fehlgeschlagen | Error-Icon + Message | E2E |
| DUD-UP05 | Datei entfernen (vor Upload) | Aus Liste entfernt | E2E |

---

## 3. CollectionShareDialog

**Datei:** `src/components/RAG/CollectionShareDialog.vue`
**Trigger:** Collection → Teilen Button

### User-Suche

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CSD-S01 | Tippen | Suchergebnisse erscheinen | E2E |
| CSD-S02 | User auswählen | User zur Liste hinzugefügt | E2E |
| CSD-S03 | Kein Ergebnis | "Keine User gefunden" | E2E |

### User-Liste

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CSD-L01 | Geteilte User angezeigt | Tags mit Namen | E2E |
| CSD-L02 | X klicken | User entfernt | E2E |
| CSD-L03 | Leere Liste | Hinweistext | E2E |

### Speichern

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CSD-SV01 | Speichern klicken | API-Call erfolgreich | E2E |
| CSD-SV02 | Abbrechen klicken | Änderungen verworfen | E2E |

---

## 4. ChatbotTestDialog

**Datei:** `src/components/Admin/ChatbotAdmin/ChatbotTestDialog.vue`
**Trigger:** Chatbot Editor → Testen Button

### Chat-Interface

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CTD-C01 | Welcome Message | Bot-Nachricht angezeigt | E2E |
| CTD-C02 | Nachricht senden | User-Nachricht erscheint | E2E |
| CTD-C03 | Bot antwortet | Bot-Nachricht erscheint | E2E |
| CTD-C04 | Streaming | Token-by-Token | E2E |

### Sources

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CTD-S01 | Sources angezeigt | Chips unter Antwort | E2E |
| CTD-S02 | Source klicken | Detail-Dialog öffnet | E2E |
| CTD-S03 | Relevanz-Score | Score angezeigt | E2E |

### Settings-Panel

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CTD-P01 | Settings toggle | Panel öffnet/schließt | E2E |
| CTD-P02 | Temperature Slider | Wert änderbar | E2E |
| CTD-P03 | Max Tokens Slider | Wert änderbar | E2E |
| CTD-P04 | Top-K Slider | Wert änderbar | E2E |
| CTD-P05 | Min Relevance Slider | Wert änderbar | E2E |
| CTD-P06 | System Prompt | Text änderbar | E2E |
| CTD-P07 | Reset Settings | Zurück zu Defaults | E2E |

### Fullscreen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CTD-F01 | Fullscreen Button | Dialog wird Vollbild | E2E |
| CTD-F02 | Exit Fullscreen | Zurück zur Normal-Größe | E2E |

---

## 5. TestPromptDialog

**Datei:** `src/components/PromptEngineering/TestPromptDialog.vue`
**Trigger:** Prompt Engineering → Testen Button

### Konfiguration

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TPD-K01 | Model Dropdown | Models angezeigt | E2E |
| TPD-K02 | Model auswählen | Auswahl gesetzt | E2E |
| TPD-K03 | Temperature Slider | Wert änderbar | E2E |
| TPD-K04 | Max Tokens Input | Wert änderbar | E2E |

### JSON Mode

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TPD-J01 | JSON Mode Toggle | Schema-Editor erscheint | E2E |
| TPD-J02 | Schema eingeben | Validiert | E2E |
| TPD-J03 | Response ist JSON | Korrektes Format | E2E |

### Examples

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TPD-E01 | Examples angezeigt | Chips sichtbar | E2E |
| TPD-E02 | Example auswählen | Preview angezeigt | E2E |
| TPD-E03 | Example in Prompt | Daten substituiert | E2E |

### Streaming

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TPD-S01 | Test starten | Streaming beginnt | E2E |
| TPD-S02 | Progress-Bar | Animiert während Streaming | E2E |
| TPD-S03 | Token erscheinen | Stück für Stück | E2E |
| TPD-S04 | Regenerate Button | Neuer Test startet | E2E |

---

## 6. CollectionAssignmentDialog

**Datei:** `src/components/Admin/ChatbotAdmin/CollectionAssignmentDialog.vue`
**Trigger:** Chatbot Editor → Collections verwalten

### Layout

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CAD-L01 | Zwei-Spalten-Layout | Links: Assigned, Rechts: Available | E2E |
| CAD-L02 | Responsive | Stack auf Mobile | E2E |

### Zugewiesene Collections

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CAD-A01 | Collections angezeigt | Mit Priorität (#1, #2) | E2E |
| CAD-A02 | Drag Handle | Sichtbar und ziehbar | E2E |
| CAD-A03 | Entfernen Button | Collection entfernt | E2E |
| CAD-A04 | Empty State | "Keine Collections" | E2E |

### Verfügbare Collections

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CAD-V01 | Collections angezeigt | Mit Add-Button | E2E |
| CAD-V02 | Suche | Filtert Liste | E2E |
| CAD-V03 | Hinzufügen | Wechselt zu Assigned | E2E |

### Drag & Drop

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CAD-D01 | Drag starten | Element visuell bewegt | E2E |
| CAD-D02 | Drop | Neue Reihenfolge | E2E |
| CAD-D03 | Prioritäten aktualisiert | #1, #2, #3... | E2E |

---

## 7. AuthenticityStatsDialog

**Datei:** `src/components/Admin/sections/AuthenticityStatsDialog.vue`
**Trigger:** Admin → Szenarien → Stats Button

### Metriken

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ASD-M01 | Krippendorff's Alpha | Wert angezeigt | E2E |
| ASD-M02 | Overall Accuracy | Prozent angezeigt | E2E |
| ASD-M03 | Progress | Mit Progress-Bar | E2E |
| ASD-M04 | Total Threads | Zahl angezeigt | E2E |

### Vote Distribution

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ASD-V01 | Bar Chart | Horizontal gestapelt | E2E |
| ASD-V02 | Real Segment | Grün | Visual |
| ASD-V03 | Fake Segment | Rot | Visual |
| ASD-V04 | Pending Segment | Grau | Visual |

### User-Tabelle

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ASD-T01 | User-Liste | Alle Rater angezeigt | E2E |
| ASD-T02 | Suche | Filtert nach Username | E2E |
| ASD-T03 | Klick auf User | Details angezeigt | E2E |

### Fullscreen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ASD-F01 | Fullscreen Toggle | Vollbild-Ansicht | E2E |
| ASD-F02 | User-Panel | Seitlich eingeblendet | E2E |

---

## 8. KaimoHintAssignmentDialog

**Datei:** `src/components/Kaimo/KaimoHintAssignmentDialog.vue`
**Trigger:** KAIMO → Kategorie klicken

### Hints

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| KHD-H01 | Hints angezeigt | Liste aller Hints | E2E |
| KHD-H02 | Leere Kategorie | "Keine Hints" | E2E |

### Zuweisung

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| KHD-A01 | Subcategory Dropdown | Auswahl möglich | E2E |
| KHD-A02 | Risk-Button | Rot markiert | E2E |
| KHD-A03 | Resource-Button | Grün markiert | E2E |
| KHD-A04 | Unclear-Button | Grau markiert | E2E |
| KHD-A05 | Save Button | Enabled wenn komplett | E2E |
| KHD-A06 | Reset Button | Zuweisung entfernt | E2E |

---

## 9. ScenarioDetailsDialog

**Datei:** `src/components/parts/ScenarioDetailsDialog.vue`
**Trigger:** Admin → Szenarien → Details/Bearbeiten

### View Mode

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SDD-V01 | Name angezeigt | Korrekt | E2E |
| SDD-V02 | Kategorie angezeigt | Korrekt | E2E |
| SDD-V03 | Datum angezeigt | Start-End | E2E |
| SDD-V04 | Edit Button | Wechselt zu Edit | E2E |

### Edit Mode

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SDD-E01 | Name editierbar | Text änderbar | E2E |
| SDD-E02 | Datum editierbar | Date-Picker öffnet | E2E |
| SDD-E03 | Users Panel | Erweitert/Kollabiert | E2E |
| SDD-E04 | Threads Panel | Erweitert/Kollabiert | E2E |

### User-Zuweisung

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SDD-U01 | Rater angezeigt | Mit Cards | E2E |
| SDD-U02 | Viewer angezeigt | Mit Cards | E2E |
| SDD-U03 | User hinzufügen | Checkbox-Auswahl | E2E |
| SDD-U04 | User entfernen | Aus Liste entfernt | E2E |

### Thread-Zuweisung

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SDD-TH01 | Threads angezeigt | Mit Subject | E2E |
| SDD-TH02 | Thread-Filter | Von-Bis Filter | E2E |
| SDD-TH03 | Alle auswählen | Alle Checkboxes | E2E |
| SDD-TH04 | Thread hinzufügen | Checkbox-Auswahl | E2E |

### Speichern

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SDD-S01 | Speichern klicken | Bestätigungsdialog | E2E |
| SDD-S02 | Bestätigen | API-Call erfolgreich | E2E |
| SDD-S03 | Abbrechen | Änderungen verworfen | E2E |

---

## 10. Test-Code für Dialoge

```typescript
// e2e/dialogs/user-settings.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('UserSettingsDialog', () => {
  test('USD-O01: dialog opens from user menu', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')
    await authenticatedPage.click('[data-test="user-menu"]')
    await authenticatedPage.click('[data-test="settings-button"]')
    await expect(authenticatedPage.locator('.v-dialog')).toBeVisible()
  })

  test('USD-C03: collab color saves', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')
    // Open settings
    await authenticatedPage.click('[data-test="user-menu"]')
    await authenticatedPage.click('[data-test="settings-button"]')

    // Select color
    await authenticatedPage.click('.color-option:nth-child(3)')

    // Save
    await authenticatedPage.click('button:has-text("Fertig")')

    // Verify API call
    await expect(authenticatedPage.locator('.v-snackbar')).toContainText('gespeichert')
  })

  test('USD-A05: avatar rate limit', async ({ authenticatedPage }) => {
    // After 3 changes, should show rate limit warning
    await authenticatedPage.goto('/Home')
    await authenticatedPage.click('[data-test="user-menu"]')
    await authenticatedPage.click('[data-test="settings-button"]')

    // Try to change avatar 4 times
    for (let i = 0; i < 4; i++) {
      await authenticatedPage.click('[data-test="regenerate-avatar"]')
    }

    await expect(authenticatedPage.locator('.rate-limit-warning')).toBeVisible()
  })
})
```

```typescript
// e2e/dialogs/document-upload.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('DocumentUploadDialog', () => {
  test('DUD-DD01: drag and drop highlight', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=rag')
    await adminPage.click('[data-test="upload-button"]')

    const dropzone = adminPage.locator('.drop-zone')

    // Simulate drag over
    await dropzone.dispatchEvent('dragenter')
    await expect(dropzone).toHaveClass(/highlighted/)
  })

  test('DUD-UP01: upload shows progress', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=rag')
    await adminPage.click('[data-test="upload-button"]')

    // Select file
    await adminPage.setInputFiles('input[type="file"]', 'e2e/fixtures/test.pdf')

    // Select collection
    await adminPage.click('.collection-select')
    await adminPage.click('.v-list-item >> nth=0')

    // Start upload
    await adminPage.click('button:has-text("Hochladen")')

    // Progress should appear
    await expect(adminPage.locator('.upload-progress')).toBeVisible()
  })
})
```

---

## 11. Checkliste für manuelle Tests

### UserSettingsDialog
- [ ] Öffnet von AppBar
- [ ] Profil-Info korrekt
- [ ] Theme wechseln funktioniert
- [ ] Collab-Farbe wählbar
- [ ] Avatar hochladen
- [ ] Avatar regenerieren
- [ ] Rate Limit erreicht

### DocumentUploadDialog
- [ ] Drag & Drop funktioniert
- [ ] Multi-File Upload
- [ ] Collection auswählen
- [ ] Progress angezeigt
- [ ] Fehler angezeigt
- [ ] Datei entfernen

### ChatbotTestDialog
- [ ] Chat funktioniert
- [ ] Streaming sichtbar
- [ ] Sources klickbar
- [ ] Settings änderbar
- [ ] Fullscreen funktioniert

### ScenarioDetailsDialog
- [ ] View Mode korrekt
- [ ] Edit Mode funktioniert
- [ ] User hinzufügen/entfernen
- [ ] Threads zuweisen
- [ ] Speichern mit Bestätigung

---

**Letzte Aktualisierung:** 30. Dezember 2025
