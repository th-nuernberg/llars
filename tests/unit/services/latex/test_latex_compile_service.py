"""
Unit Tests: LaTeX Compile Service
=================================

Tests for the LaTeX compilation service.

Test IDs:
- LATEX-001 to LATEX-015: Path Helper Functions
- LATEX-020 to LATEX-035: Workspace Snapshot
- LATEX-040 to LATEX-055: Main TeX Selection
- LATEX-060 to LATEX-075: SyncTeX Parsing
- LATEX-080 to LATEX-095: Compile Job (mocked)
- LATEX-100 to LATEX-110: Node Finding

Status: Implemented
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestPathHelpers:
    """
    Path Helper Functions Tests

    Tests for path manipulation helper functions.
    """

    def test_LATEX_001_safe_relative_path_valid(self, app, app_context):
        """
        [LATEX-001] Safe Relative Path - Valid

        Gültige relative Pfade sollten zurückgegeben werden.
        """
        from services.latex_compile_service import _safe_relative_path

        assert _safe_relative_path('main.tex') == 'main.tex'
        assert _safe_relative_path('sections/intro.tex') == 'sections/intro.tex'
        assert _safe_relative_path('  main.tex  ') == 'main.tex'

    def test_LATEX_002_safe_relative_path_backslash(self, app, app_context):
        """
        [LATEX-002] Safe Relative Path - Backslash

        Backslashes sollten zu Forward Slashes konvertiert werden.
        """
        from services.latex_compile_service import _safe_relative_path

        result = _safe_relative_path('sections\\intro.tex')
        assert '\\' not in result

    def test_LATEX_003_safe_relative_path_parent_traversal(self, app, app_context):
        """
        [LATEX-003] Safe Relative Path - Parent Traversal

        Parent Directory Traversal sollte Fehler werfen.
        """
        from services.latex_compile_service import _safe_relative_path, LatexCompileError

        with pytest.raises(LatexCompileError, match="Invalid path"):
            _safe_relative_path('../etc/passwd')

        with pytest.raises(LatexCompileError, match="Invalid path"):
            _safe_relative_path('../../secret')

    def test_LATEX_004_safe_relative_path_absolute(self, app, app_context):
        """
        [LATEX-004] Safe Relative Path - Absolute

        Absolute Pfade sollten Fehler werfen.
        """
        from services.latex_compile_service import _safe_relative_path, LatexCompileError

        with pytest.raises(LatexCompileError, match="Invalid path"):
            _safe_relative_path('/etc/passwd')

    def test_LATEX_005_normalize_path_basic(self, app, app_context):
        """
        [LATEX-005] Normalize Path - Basic

        Pfade sollten normalisiert werden.
        """
        from services.latex_compile_service import _normalize_path

        assert _normalize_path('main.tex') == 'main.tex'
        assert _normalize_path('./main.tex') == 'main.tex'
        assert _normalize_path('/main.tex') == 'main.tex'
        assert _normalize_path('') == ''

    def test_LATEX_006_normalize_path_backslash(self, app, app_context):
        """
        [LATEX-006] Normalize Path - Backslash

        Backslashes sollten konvertiert werden.
        """
        from services.latex_compile_service import _normalize_path

        result = _normalize_path('sections\\intro.tex')
        assert result == 'sections/intro.tex'

    def test_LATEX_007_parse_float_valid(self, app, app_context):
        """
        [LATEX-007] Parse Float - Valid

        Gültige Floats sollten geparsed werden.
        """
        from services.latex_compile_service import _parse_float

        assert _parse_float('3.14') == 3.14
        assert _parse_float('42') == 42.0
        assert _parse_float('-1.5') == -1.5

    def test_LATEX_008_parse_float_invalid(self, app, app_context):
        """
        [LATEX-008] Parse Float - Invalid

        Ungültige Werte sollten None zurückgeben.
        """
        from services.latex_compile_service import _parse_float

        assert _parse_float('abc') is None
        assert _parse_float('') is None
        assert _parse_float(None) is None


class TestDocPath:
    """
    Document Path Tests

    Tests for building document paths from hierarchy.
    """

    def test_LATEX_010_doc_path_simple(self, app, app_context):
        """
        [LATEX-010] Doc Path - Simple

        Einfacher Pfad ohne Parent sollte nur Titel sein.
        """
        from services.latex_compile_service import _doc_path

        mock_doc = MagicMock()
        mock_doc.parent_id = None
        mock_doc.title = 'main.tex'

        docs_by_id = {1: mock_doc}
        cache = {}

        result = _doc_path(1, docs_by_id, cache)

        assert result == 'main.tex'

    def test_LATEX_011_doc_path_nested(self, app, app_context):
        """
        [LATEX-011] Doc Path - Nested

        Verschachtelte Dokumente sollten vollständigen Pfad haben.
        """
        from services.latex_compile_service import _doc_path

        parent_doc = MagicMock()
        parent_doc.parent_id = None
        parent_doc.title = 'sections'

        child_doc = MagicMock()
        child_doc.parent_id = 1
        child_doc.title = 'intro.tex'

        docs_by_id = {1: parent_doc, 2: child_doc}
        cache = {}

        result = _doc_path(2, docs_by_id, cache)

        assert result == 'sections/intro.tex'

    def test_LATEX_012_doc_path_cached(self, app, app_context):
        """
        [LATEX-012] Doc Path - Cached

        Gecachte Pfade sollten wiederverwendet werden.
        """
        from services.latex_compile_service import _doc_path

        docs_by_id = {}
        cache = {1: 'cached/path.tex'}

        result = _doc_path(1, docs_by_id, cache)

        assert result == 'cached/path.tex'

    def test_LATEX_013_doc_path_not_found(self, app, app_context):
        """
        [LATEX-013] Doc Path - Not Found

        Nicht existierendes Dokument sollte leeren String zurückgeben.
        """
        from services.latex_compile_service import _doc_path

        result = _doc_path(999, {}, {})

        assert result == ''


class TestWorkspaceSnapshot:
    """
    Workspace Snapshot Tests

    Tests for building workspace snapshots.
    """

    def test_LATEX_020_build_workspace_snapshot_success(self, app, db, app_context):
        """
        [LATEX-020] Build Workspace Snapshot - Success

        Snapshot sollte erfolgreich gebaut werden.
        """
        from services.latex_compile_service import build_workspace_snapshot
        from db.models.latex_collab import (
            LatexWorkspace, LatexDocument, LatexNodeType
        )

        # Create workspace
        workspace = LatexWorkspace(
            name='Test Workspace',
            owner_username='testuser'
        )
        db.session.add(workspace)
        db.session.flush()

        # Create document
        doc = LatexDocument(
            workspace_id=workspace.id,
            title='main.tex',
            node_type=LatexNodeType.file,
            content_text='\\documentclass{article}'
        )
        db.session.add(doc)
        db.session.commit()

        # Test
        snapshot = build_workspace_snapshot(workspace.id)

        assert snapshot['workspace_id'] == workspace.id
        assert 'nodes' in snapshot
        assert len(snapshot['nodes']) == 1
        assert snapshot['nodes'][0]['title'] == 'main.tex'

    def test_LATEX_021_build_workspace_snapshot_not_found(self, app, db, app_context):
        """
        [LATEX-021] Build Workspace Snapshot - Not Found

        Nicht existierender Workspace sollte Fehler werfen.
        """
        from services.latex_compile_service import build_workspace_snapshot, LatexCompileError

        with pytest.raises(LatexCompileError, match="Workspace not found"):
            build_workspace_snapshot(99999)

    def test_LATEX_022_build_workspace_snapshot_with_folder(self, app, db, app_context):
        """
        [LATEX-022] Build Workspace Snapshot - With Folder

        Snapshot mit Ordner-Struktur sollte korrekt sein.
        """
        from services.latex_compile_service import build_workspace_snapshot
        from db.models.latex_collab import (
            LatexWorkspace, LatexDocument, LatexNodeType
        )

        workspace = LatexWorkspace(
            name='Test Workspace 2',
            owner_username='testuser'
        )
        db.session.add(workspace)
        db.session.flush()

        # Create folder
        folder = LatexDocument(
            workspace_id=workspace.id,
            title='sections',
            node_type=LatexNodeType.folder
        )
        db.session.add(folder)
        db.session.flush()

        # Create file in folder
        doc = LatexDocument(
            workspace_id=workspace.id,
            parent_id=folder.id,
            title='intro.tex',
            node_type=LatexNodeType.file,
            content_text='\\section{Introduction}'
        )
        db.session.add(doc)
        db.session.commit()

        snapshot = build_workspace_snapshot(workspace.id)

        assert len(snapshot['nodes']) == 2
        # Find the nested file
        nested_file = next((n for n in snapshot['nodes'] if n['title'] == 'intro.tex'), None)
        assert nested_file is not None
        assert nested_file['path'] == 'sections/intro.tex'


class TestPickMainTex:
    """
    Main TeX Selection Tests

    Tests for selecting the main TeX file.
    """

    def test_LATEX_040_pick_main_tex_by_id(self, app, app_context):
        """
        [LATEX-040] Pick Main TeX - By ID

        Main Document ID sollte bevorzugt werden.
        """
        from services.latex_compile_service import _pick_main_tex

        snapshot = {
            'main_document_id': 1,
            'nodes': [
                {'id': 1, 'path': 'document.tex', 'node_type': 'file'},
                {'id': 2, 'path': 'main.tex', 'node_type': 'file'},
            ]
        }

        result = _pick_main_tex(snapshot)

        assert result == 'document.tex'

    def test_LATEX_041_pick_main_tex_fallback_main(self, app, app_context):
        """
        [LATEX-041] Pick Main TeX - Fallback to main.tex

        Ohne main_document_id sollte main.tex verwendet werden.
        """
        from services.latex_compile_service import _pick_main_tex

        snapshot = {
            'main_document_id': None,
            'nodes': [
                {'id': 1, 'path': 'other.tex', 'node_type': 'file'},
                {'id': 2, 'path': 'main.tex', 'node_type': 'file'},
            ]
        }

        result = _pick_main_tex(snapshot)

        assert result == 'main.tex'

    def test_LATEX_042_pick_main_tex_nested_main(self, app, app_context):
        """
        [LATEX-042] Pick Main TeX - Nested main.tex

        Verschachtelte main.tex sollte gefunden werden.
        """
        from services.latex_compile_service import _pick_main_tex

        snapshot = {
            'main_document_id': None,
            'nodes': [
                {'id': 1, 'path': 'sections/intro.tex', 'node_type': 'file'},
                {'id': 2, 'path': 'src/main.tex', 'node_type': 'file'},
            ]
        }

        result = _pick_main_tex(snapshot)

        assert result == 'src/main.tex'

    def test_LATEX_043_pick_main_tex_first_tex(self, app, app_context):
        """
        [LATEX-043] Pick Main TeX - First .tex File

        Ohne main.tex sollte erste .tex Datei verwendet werden.
        """
        from services.latex_compile_service import _pick_main_tex

        snapshot = {
            'main_document_id': None,
            'nodes': [
                {'id': 1, 'path': 'document.tex', 'node_type': 'file'},
                {'id': 2, 'path': 'appendix.tex', 'node_type': 'file'},
            ]
        }

        result = _pick_main_tex(snapshot)

        assert result == 'document.tex'

    def test_LATEX_044_pick_main_tex_no_tex_files(self, app, app_context):
        """
        [LATEX-044] Pick Main TeX - No .tex Files

        Ohne .tex Dateien sollte None zurückgegeben werden.
        """
        from services.latex_compile_service import _pick_main_tex

        snapshot = {
            'main_document_id': None,
            'nodes': [
                {'id': 1, 'path': 'image.png', 'node_type': 'file'},
                {'id': 2, 'path': 'refs.bib', 'node_type': 'file'},
            ]
        }

        result = _pick_main_tex(snapshot)

        assert result is None

    def test_LATEX_045_pick_main_tex_folder_excluded(self, app, app_context):
        """
        [LATEX-045] Pick Main TeX - Folder Excluded

        Ordner sollten nicht als main.tex ausgewählt werden.
        """
        from services.latex_compile_service import _pick_main_tex

        snapshot = {
            'main_document_id': 1,
            'nodes': [
                {'id': 1, 'path': 'main.tex', 'node_type': 'folder'},  # Folder, not file!
                {'id': 2, 'path': 'document.tex', 'node_type': 'file'},
            ]
        }

        result = _pick_main_tex(snapshot)

        # Should not pick the folder, should fall back
        assert result == 'document.tex'


class TestSynctexParsing:
    """
    SyncTeX Parsing Tests

    Tests for parsing SyncTeX output.
    """

    def test_LATEX_060_parse_synctex_view_success(self, app, app_context):
        """
        [LATEX-060] Parse SyncTeX View - Success

        SyncTeX View Output sollte korrekt geparsed werden.
        """
        from services.latex_compile_service import _parse_synctex_view

        output = """SyncTeX result:
Page:1
x:72.0
y:700.0
h:72.0
v:700.0
W:500.0
H:20.0"""

        result = _parse_synctex_view(output)

        assert result['page'] == 1
        assert result['x'] == 72.0
        assert result['y'] == 700.0

    def test_LATEX_061_parse_synctex_view_with_hv(self, app, app_context):
        """
        [LATEX-061] Parse SyncTeX View - With h/v fallback

        h/v Werte sollten als x/y Fallback verwendet werden.
        """
        from services.latex_compile_service import _parse_synctex_view

        output = """Page:2
h:100.5
v:200.5"""

        result = _parse_synctex_view(output)

        assert result['page'] == 2
        assert result['x'] == 100.5
        assert result['y'] == 200.5

    def test_LATEX_062_parse_synctex_view_missing_data(self, app, app_context):
        """
        [LATEX-062] Parse SyncTeX View - Missing Data

        Fehlende Daten sollten Fehler werfen.
        """
        from services.latex_compile_service import _parse_synctex_view, LatexCompileError

        output = """Page:1
h:72.0"""  # Missing y/v

        with pytest.raises(LatexCompileError, match="no location"):
            _parse_synctex_view(output)

    def test_LATEX_063_parse_synctex_edit_success(self, app, app_context):
        """
        [LATEX-063] Parse SyncTeX Edit - Success

        SyncTeX Edit Output sollte korrekt geparsed werden.
        """
        from services.latex_compile_service import _parse_synctex_edit

        output = """SyncTeX result:
Input:42:5:main.tex"""

        result = _parse_synctex_edit(output)

        assert result['line'] == 42
        assert result['column'] == 5
        assert result['path'] == 'main.tex'

    def test_LATEX_064_parse_synctex_edit_full_path(self, app, app_context):
        """
        [LATEX-064] Parse SyncTeX Edit - Full Path

        Vollständiger Pfad sollte geparsed werden.
        """
        from services.latex_compile_service import _parse_synctex_edit

        output = """Input:10:1:/tmp/latex_ws_1/sections/intro.tex"""

        result = _parse_synctex_edit(output)

        assert result['line'] == 10
        assert result['column'] == 1
        assert 'intro.tex' in result['path']

    def test_LATEX_065_parse_synctex_edit_no_input(self, app, app_context):
        """
        [LATEX-065] Parse SyncTeX Edit - No Input

        Fehlende Input-Zeile sollte Fehler werfen.
        """
        from services.latex_compile_service import _parse_synctex_edit, LatexCompileError

        output = """SyncTeX result:
Page:1
x:72.0"""

        with pytest.raises(LatexCompileError, match="no source location"):
            _parse_synctex_edit(output)


class TestNodeFinding:
    """
    Node Finding Tests

    Tests for finding nodes in snapshots.
    """

    def test_LATEX_100_find_node_by_id(self, app, app_context):
        """
        [LATEX-100] Find Node - By ID

        Node sollte nach ID gefunden werden.
        """
        from services.latex_compile_service import _find_node

        snapshot = {
            'nodes': [
                {'id': 1, 'path': 'main.tex'},
                {'id': 2, 'path': 'intro.tex'},
            ]
        }

        result = _find_node(snapshot, 2)

        assert result is not None
        assert result['path'] == 'intro.tex'

    def test_LATEX_101_find_node_not_found(self, app, app_context):
        """
        [LATEX-101] Find Node - Not Found

        Nicht existierender Node sollte None zurückgeben.
        """
        from services.latex_compile_service import _find_node

        snapshot = {'nodes': [{'id': 1, 'path': 'main.tex'}]}

        result = _find_node(snapshot, 999)

        assert result is None

    def test_LATEX_102_find_node_by_path(self, app, app_context):
        """
        [LATEX-102] Find Node by Path

        Node sollte nach Pfad gefunden werden.
        """
        from services.latex_compile_service import _find_node_by_path

        snapshot = {
            'nodes': [
                {'id': 1, 'path': 'main.tex'},
                {'id': 2, 'path': 'sections/intro.tex'},
            ]
        }

        result = _find_node_by_path(snapshot, 'sections/intro.tex')

        assert result is not None
        assert result['id'] == 2

    def test_LATEX_103_find_node_by_path_normalized(self, app, app_context):
        """
        [LATEX-103] Find Node by Path - Normalized

        Pfad sollte normalisiert werden beim Suchen.
        """
        from services.latex_compile_service import _find_node_by_path

        snapshot = {
            'nodes': [
                {'id': 1, 'path': 'sections/intro.tex'},
            ]
        }

        # Should find with leading ./
        result = _find_node_by_path(snapshot, './sections/intro.tex')

        assert result is not None
        assert result['id'] == 1

    def test_LATEX_104_find_node_by_path_empty(self, app, app_context):
        """
        [LATEX-104] Find Node by Path - Empty

        Leerer Pfad sollte None zurückgeben.
        """
        from services.latex_compile_service import _find_node_by_path

        snapshot = {'nodes': [{'id': 1, 'path': 'main.tex'}]}

        assert _find_node_by_path(snapshot, '') is None
        assert _find_node_by_path(snapshot, None) is None


class TestCompileJobMocked:
    """
    Compile Job Tests (Mocked)

    Tests for compile job execution with mocked subprocess.
    """

    def test_LATEX_080_run_compile_job_not_found(self, app, db, app_context):
        """
        [LATEX-080] Run Compile Job - Not Found

        Nicht existierender Job sollte nichts tun.
        """
        from services.latex_compile_service import run_compile_job

        # Should not raise
        run_compile_job(99999)

    def test_LATEX_081_run_compile_job_workspace_not_found(self, app, db, app_context):
        """
        [LATEX-081] Run Compile Job - Workspace Not Found

        Job ohne Workspace sollte fehlschlagen.
        """
        from services.latex_compile_service import run_compile_job
        from db.models.latex_collab import LatexCompileJob

        # Create job with invalid workspace
        job = LatexCompileJob(
            workspace_id=99999,
            status='queued'
        )
        db.session.add(job)
        db.session.commit()

        run_compile_job(job.id)

        # Refresh
        db.session.refresh(job)
        assert job.status == 'failed'
        assert 'Workspace not found' in job.error_message

    def test_LATEX_082_run_compile_job_no_tex_file(self, app, db, app_context):
        """
        [LATEX-082] Run Compile Job - No TeX File

        Workspace ohne .tex Datei sollte fehlschlagen.
        """
        from services.latex_compile_service import run_compile_job
        from db.models.latex_collab import (
            LatexWorkspace, LatexDocument, LatexCompileJob, LatexNodeType
        )

        # Create workspace without .tex file
        workspace = LatexWorkspace(
            name='No TeX Workspace',
            owner_username='testuser'
        )
        db.session.add(workspace)
        db.session.flush()

        doc = LatexDocument(
            workspace_id=workspace.id,
            title='readme.md',
            node_type=LatexNodeType.file,
            content_text='# Readme'
        )
        db.session.add(doc)
        db.session.flush()

        job = LatexCompileJob(
            workspace_id=workspace.id,
            status='queued'
        )
        db.session.add(job)
        db.session.commit()

        run_compile_job(job.id)

        db.session.refresh(job)
        assert job.status == 'failed'
        assert 'No main .tex file' in job.error_message

    @patch('services.latex_compile_service.subprocess.run')
    def test_LATEX_083_run_compile_job_success(self, mock_run, app, db, app_context):
        """
        [LATEX-083] Run Compile Job - Success (Mocked)

        Erfolgreiche Kompilierung sollte PDF speichern.
        """
        import tempfile
        import os
        from services.latex_compile_service import run_compile_job
        from db.models.latex_collab import (
            LatexWorkspace, LatexDocument, LatexCompileJob, LatexNodeType
        )

        # Create workspace with .tex file
        workspace = LatexWorkspace(
            name='Compile Test',
            owner_username='testuser'
        )
        db.session.add(workspace)
        db.session.flush()

        doc = LatexDocument(
            workspace_id=workspace.id,
            title='main.tex',
            node_type=LatexNodeType.file,
            content_text='\\documentclass{article}\\begin{document}Hello\\end{document}'
        )
        db.session.add(doc)
        db.session.flush()

        job = LatexCompileJob(
            workspace_id=workspace.id,
            status='queued'
        )
        db.session.add(job)
        db.session.commit()

        # Mock subprocess to create PDF
        def mock_subprocess(cmd, **kwargs):
            cwd = kwargs.get('cwd')
            if cwd:
                # Create fake PDF
                pdf_path = os.path.join(cwd, 'main.pdf')
                with open(pdf_path, 'wb') as f:
                    f.write(b'%PDF-1.4 fake pdf content')
            result = MagicMock()
            result.stdout = 'Output log'
            result.returncode = 0
            return result

        mock_run.side_effect = mock_subprocess

        run_compile_job(job.id)

        db.session.refresh(job)
        assert job.status == 'success'
        assert job.pdf_blob is not None

    @patch('services.latex_compile_service.subprocess.run')
    def test_LATEX_084_run_compile_job_failed(self, mock_run, app, db, app_context):
        """
        [LATEX-084] Run Compile Job - Failed (Mocked)

        Fehlgeschlagene Kompilierung sollte Status 'failed' haben.
        """
        from services.latex_compile_service import run_compile_job
        from db.models.latex_collab import (
            LatexWorkspace, LatexDocument, LatexCompileJob, LatexNodeType
        )

        workspace = LatexWorkspace(
            name='Fail Test',
            owner_username='testuser'
        )
        db.session.add(workspace)
        db.session.flush()

        doc = LatexDocument(
            workspace_id=workspace.id,
            title='main.tex',
            node_type=LatexNodeType.file,
            content_text='\\invalid latex'
        )
        db.session.add(doc)
        db.session.flush()

        job = LatexCompileJob(
            workspace_id=workspace.id,
            status='queued'
        )
        db.session.add(job)
        db.session.commit()

        # Mock subprocess - don't create PDF (simulating failure)
        mock_run.return_value = MagicMock(stdout='Error: undefined control sequence', returncode=1)

        run_compile_job(job.id)

        db.session.refresh(job)
        assert job.status == 'failed'
        assert job.pdf_blob is None


class TestSynctexSearchMocked:
    """
    SyncTeX Search Tests (Mocked)

    Tests for SyncTeX forward/inverse search with mocked subprocess.
    """

    def test_LATEX_090_synctex_forward_job_not_found(self, app, db, app_context):
        """
        [LATEX-090] SyncTeX Forward - Job Not Found

        Nicht existierender Job sollte Fehler werfen.
        """
        from services.latex_compile_service import synctex_forward_search, LatexCompileError

        with pytest.raises(LatexCompileError, match="Compile job not found"):
            synctex_forward_search(99999, 1, 10)

    def test_LATEX_091_synctex_inverse_job_not_found(self, app, db, app_context):
        """
        [LATEX-091] SyncTeX Inverse - Job Not Found

        Nicht existierender Job sollte Fehler werfen.
        """
        from services.latex_compile_service import synctex_inverse_search, LatexCompileError

        with pytest.raises(LatexCompileError, match="Compile job not found"):
            synctex_inverse_search(99999, 1, 72.0, 700.0)
