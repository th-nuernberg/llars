# Feature Testanforderungen: LaTeX Kompilierung

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für die LaTeX-Kompilierung und den LaTeX Collaborative Editor.

**Komponenten:** LaTeX Editor | PDF Compilation | BibTeX | Real-time Collab

---

## 1. LaTeX Editor

**Komponente:** `LatexCollab.vue`
**API:** `/api/latex-collab/workspaces`, `/api/latex-collab/documents`

### Workspace Management

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-W01 | Workspace erstellen | 201, Workspace ID | Integration |
| LTX-W02 | Workspace laden | Dokumente zurück | Integration |
| LTX-W03 | Workspace umbenennen | Name aktualisiert | Integration |
| LTX-W04 | Workspace löschen | Cascade Delete | Integration |
| LTX-W05 | Workspace teilen | Sharing funktioniert | Integration |
| LTX-W06 | Shared Workspace sehen | In Liste sichtbar | Integration |
| LTX-W07 | Unshare Workspace | Zugriff entfernt | Integration |

### Document Management

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-D01 | Document erstellen | Neues Dokument | Integration |
| LTX-D02 | Document umbenennen | Name aktualisiert | Integration |
| LTX-D03 | Document löschen | Soft Delete | Integration |
| LTX-D04 | Main Document setzen | is_main=true | Integration |
| LTX-D05 | Document Reihenfolge | Sort Order | Integration |

---

## 2. PDF Kompilierung

**API:** `POST /api/latex-collab/workspaces/:id/compile`
**Service:** LaTeX Compiler Service

### Basic Compilation

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-C01 | Simple Document | PDF erstellt | Integration |
| LTX-C02 | Document mit Sections | PDF mit TOC | Integration |
| LTX-C03 | Document mit Bildern | Bilder eingebettet | Integration |
| LTX-C04 | Document mit Tabellen | Tabellen gerendert | Integration |
| LTX-C05 | Multi-File Project | Includes funktionieren | Integration |
| LTX-C06 | Math Formulas | Formeln korrekt | Integration |

### Error Handling

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-E01 | Syntax Error | Error Message | Integration |
| LTX-E02 | Missing Package | Package Error | Integration |
| LTX-E03 | Missing File | Include Error | Integration |
| LTX-E04 | Infinite Loop | Timeout | Integration |
| LTX-E05 | Invalid UTF-8 | Encoding Error | Integration |

### BibTeX

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-B01 | Bibliography | References gerendert | Integration |
| LTX-B02 | Citations | \cite{} funktioniert | Integration |
| LTX-B03 | Missing Reference | Warning | Integration |
| LTX-B04 | BibTeX Style | Style angewendet | Integration |

### PDF Output

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-P01 | PDF Download | application/pdf | Integration |
| LTX-P02 | PDF Preview | Im Browser anzeigbar | Integration |
| LTX-P03 | PDF Size | Reasonable Size | Integration |
| LTX-P04 | PDF Metadata | Title, Author | Integration |
| LTX-P05 | PDF Versioning | Alte Versionen abrufbar | Integration |

---

## 3. Real-time Collaboration

**Service:** YJS + WebSocket
**Namespace:** `/latex-collab`

### Sync Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-Y01 | Initial Sync | Content geladen | Integration |
| LTX-Y02 | Edit Sync | Änderungen propagiert | Integration |
| LTX-Y03 | Multi-User Sync | Alle sehen Updates | E2E |
| LTX-Y04 | Conflict Resolution | CRDT Merge | Integration |
| LTX-Y05 | Offline Edits | Nach Reconnect sync | Integration |

### Awareness

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-A01 | User Cursor | Andere Cursor sichtbar | E2E |
| LTX-A02 | User Color | Collab-Farbe korrekt | E2E |
| LTX-A03 | User Join | Join Event | Integration |
| LTX-A04 | User Leave | Leave Event | Integration |

---

## 4. LaTeX AI (Optional Feature)

**API:** `/api/latex-collab/ai`
**Permission:** `feature:latex_collab:ai`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTXAI-01 | AI Suggestion | Text-Vorschlag | Integration |
| LTXAI-02 | AI Complete | Auto-Completion | Integration |
| LTXAI-03 | AI Fix Error | Error-Korrektur | Integration |
| LTXAI-04 | AI ohne Permission | 403 Forbidden | Integration |
| LTXAI-05 | AI Streaming | Streaming Response | Integration |

---

## 5. Test-Code

```python
# tests/integration/latex/test_compilation.py
import pytest


class TestLatexCompilation:
    """LaTeX Compilation Tests"""

    def test_LTX_C01_simple_document(self, authenticated_client, test_workspace):
        """Simple Document kompiliert zu PDF"""
        # Erst Content setzen
        authenticated_client.put(
            f'/api/latex-collab/documents/{test_workspace.main_doc.id}',
            json={'content': r'''
                \documentclass{article}
                \begin{document}
                Hello World
                \end{document}
            '''}
        )

        # Kompilieren
        response = authenticated_client.post(
            f'/api/latex-collab/workspaces/{test_workspace.id}/compile'
        )
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert len(response.data) > 0

    def test_LTX_C06_math_formulas(self, authenticated_client, test_workspace):
        """Math Formulas werden korrekt gerendert"""
        authenticated_client.put(
            f'/api/latex-collab/documents/{test_workspace.main_doc.id}',
            json={'content': r'''
                \documentclass{article}
                \usepackage{amsmath}
                \begin{document}
                $E = mc^2$
                \begin{equation}
                    \int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
                \end{equation}
                \end{document}
            '''}
        )

        response = authenticated_client.post(
            f'/api/latex-collab/workspaces/{test_workspace.id}/compile'
        )
        assert response.status_code == 200

    def test_LTX_E01_syntax_error(self, authenticated_client, test_workspace):
        """Syntax Error gibt verständliche Message"""
        authenticated_client.put(
            f'/api/latex-collab/documents/{test_workspace.main_doc.id}',
            json={'content': r'''
                \documentclass{article}
                \begin{document}
                Missing closing brace {
                \end{document}
            '''}
        )

        response = authenticated_client.post(
            f'/api/latex-collab/workspaces/{test_workspace.id}/compile'
        )
        assert response.status_code == 400
        assert 'error' in response.json
        assert 'line' in response.json or 'message' in response.json

    def test_LTX_B01_bibliography(self, authenticated_client, test_workspace):
        """Bibliography wird gerendert"""
        # Main document
        authenticated_client.put(
            f'/api/latex-collab/documents/{test_workspace.main_doc.id}',
            json={'content': r'''
                \documentclass{article}
                \begin{document}
                See \cite{test2025} for details.
                \bibliographystyle{plain}
                \bibliography{refs}
                \end{document}
            '''}
        )

        # BibTeX file
        authenticated_client.post(
            f'/api/latex-collab/workspaces/{test_workspace.id}/documents',
            json={
                'name': 'refs.bib',
                'content': '''
                    @article{test2025,
                        author = {Test Author},
                        title = {Test Title},
                        year = {2025}
                    }
                '''
            }
        )

        response = authenticated_client.post(
            f'/api/latex-collab/workspaces/{test_workspace.id}/compile'
        )
        # BibTeX benötigt mehrere Compile-Durchläufe
        assert response.status_code == 200


class TestWorkspaceManagement:
    """Workspace Management Tests"""

    def test_LTX_W01_create_workspace(self, authenticated_client):
        """Workspace erstellen"""
        response = authenticated_client.post(
            '/api/latex-collab/workspaces',
            json={'name': 'Test Workspace'}
        )
        assert response.status_code == 201
        assert 'id' in response.json

    def test_LTX_W05_share_workspace(self, authenticated_client, test_workspace, other_user):
        """Workspace teilen"""
        response = authenticated_client.post(
            f'/api/latex-collab/workspaces/{test_workspace.id}/share',
            json={'username': other_user.username, 'permission': 'edit'}
        )
        assert response.status_code == 200


class TestRealTimeCollab:
    """Real-time Collaboration Tests"""

    def test_LTX_Y02_edit_sync(self, yjs_client_1, yjs_client_2, test_document):
        """Edits werden synchronisiert"""
        # Client 1 macht Edit
        yjs_client_1.update_content(test_document.id, 'Hello from client 1')

        # Client 2 sollte Update erhalten
        import time
        time.sleep(0.5)  # Warte auf Sync
        content = yjs_client_2.get_content(test_document.id)
        assert 'Hello from client 1' in content
```

---

## 6. E2E Test-Code

```typescript
// e2e/latex/latex-collab.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('LaTeX Collaboration', () => {
  test('LTX-C01: compile simple document', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/LatexCollab')

    // Workspace erstellen
    await authenticatedPage.click('button:has-text("Neuer Workspace")')
    await authenticatedPage.fill('input[name="name"]', 'Test Workspace')
    await authenticatedPage.click('button:has-text("Erstellen")')

    // Content eingeben
    const editor = authenticatedPage.locator('.monaco-editor textarea')
    await editor.fill(String.raw`
      \documentclass{article}
      \begin{document}
      Hello World
      \end{document}
    `)

    // Kompilieren
    await authenticatedPage.click('button:has-text("Kompilieren")')

    // PDF sollte erscheinen
    await expect(authenticatedPage.locator('.pdf-preview')).toBeVisible({
      timeout: 60000
    })
  })

  test('LTX-E01: show error on syntax error', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/LatexCollab')
    // ... Workspace öffnen

    const editor = authenticatedPage.locator('.monaco-editor textarea')
    await editor.fill(String.raw`
      \documentclass{article}
      \begin{document}
      Missing brace {
      \end{document}
    `)

    await authenticatedPage.click('button:has-text("Kompilieren")')

    // Error sollte angezeigt werden
    await expect(authenticatedPage.locator('.compile-error')).toBeVisible({
      timeout: 30000
    })
    await expect(authenticatedPage.locator('.compile-error')).toContainText('error')
  })

  test('LTX-Y03: multi-user sync', async ({ browser }) => {
    // Zwei Browser-Kontexte für zwei User
    const context1 = await browser.newContext()
    const context2 = await browser.newContext()

    const page1 = await context1.newPage()
    const page2 = await context2.newPage()

    // Beide auf gleiches Dokument
    await page1.goto('/LatexCollab/workspace/1')
    await page2.goto('/LatexCollab/workspace/1')

    // User 1 tippt
    const editor1 = page1.locator('.monaco-editor textarea')
    await editor1.type('Hello from user 1')

    // User 2 sollte es sehen
    await expect(page2.locator('.monaco-editor')).toContainText('Hello from user 1', {
      timeout: 5000
    })

    await context1.close()
    await context2.close()
  })
})
```

---

## 7. Fixtures

```python
# tests/conftest.py
import pytest


@pytest.fixture
def test_workspace(authenticated_client, db):
    """LaTeX Workspace mit Main Document"""
    from app.db.models import LatexWorkspace, LatexDocument

    workspace = LatexWorkspace(
        name='Test Workspace',
        owner_id=1
    )
    db.session.add(workspace)
    db.session.flush()

    main_doc = LatexDocument(
        workspace_id=workspace.id,
        name='main.tex',
        is_main=True,
        content=r'\documentclass{article}\begin{document}\end{document}'
    )
    db.session.add(main_doc)
    db.session.commit()

    workspace.main_doc = main_doc
    return workspace


@pytest.fixture
def yjs_client_1(app, auth_token):
    """YJS Test Client 1"""
    from tests.helpers.yjs_client import YjsTestClient
    return YjsTestClient(app, auth_token)


@pytest.fixture
def yjs_client_2(app, other_user_token):
    """YJS Test Client 2"""
    from tests.helpers.yjs_client import YjsTestClient
    return YjsTestClient(app, other_user_token)
```

---

## 8. Unterstützte LaTeX-Features

### Packages (vorinstalliert)

| Package | Beschreibung |
|---------|--------------|
| `amsmath` | Mathematische Formeln |
| `graphicx` | Bilder einbinden |
| `hyperref` | Hyperlinks |
| `geometry` | Seitenränder |
| `babel` | Sprachunterstützung |
| `inputenc` | UTF-8 Encoding |
| `fontenc` | Font Encoding |
| `listings` | Code Listings |
| `tikz` | Diagramme |
| `pgfplots` | Plots |
| `biblatex` | Bibliographie |
| `natbib` | Zitationen |

### Document Classes

| Class | Beschreibung |
|-------|--------------|
| `article` | Standard Artikel |
| `report` | Längere Dokumente |
| `book` | Bücher |
| `beamer` | Präsentationen |
| `letter` | Briefe |

---

## 9. Compile-Prozess

```
1. Content sammeln (Main + Includes)
2. Temporäres Verzeichnis erstellen
3. pdflatex (1. Durchlauf)
4. biber/bibtex (wenn .bib vorhanden)
5. pdflatex (2. Durchlauf - für TOC/References)
6. pdflatex (3. Durchlauf - finale Version)
7. PDF extrahieren und speichern
8. Cleanup
```

**Timeouts:**
- pdflatex: 60 Sekunden
- biber: 30 Sekunden
- Gesamt: 180 Sekunden

---

## 10. Checkliste für manuelle Tests

### Compilation
- [ ] Simple Document kompiliert
- [ ] Document mit Bildern kompiliert
- [ ] Document mit Math kompiliert
- [ ] BibTeX funktioniert
- [ ] Fehler werden angezeigt
- [ ] PDF kann heruntergeladen werden

### Editor
- [ ] Monaco Editor lädt
- [ ] Syntax Highlighting funktioniert
- [ ] Auto-Completion funktioniert
- [ ] Undo/Redo funktioniert

### Collaboration
- [ ] Sync zwischen zwei Usern
- [ ] Cursor-Position sichtbar
- [ ] Collab-Farbe korrekt
- [ ] Offline-Edits syncen

### Workspace
- [ ] Erstellen funktioniert
- [ ] Umbenennen funktioniert
- [ ] Teilen funktioniert
- [ ] Löschen funktioniert

---

**Letzte Aktualisierung:** 30. Dezember 2025
