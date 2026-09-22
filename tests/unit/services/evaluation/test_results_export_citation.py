"""
Tests for the citation block shipped with every JSON results export.

LLARS is licensed under the PolyForm Noncommercial License 1.0.0 with an
additional citation requirement: academic work that uses LLARS — or data
produced with it — must cite the LLARS paper. The JSON export envelope
therefore carries the reference, so a researcher who only ever sees the
exported file still has the citation at hand.

Covers:
- the `citation` key is present in the ``collect_results`` envelope
- the block is handed out as a copy (no cross-export mutation)
- both route-level JSON envelopes forward it (they cherry-pick keys, so a new
  aggregate has to be wired explicitly — same regression class as the
  `timing_metrics` drop guarded by APIV1_RES_013)
- CSV / JSONL stay free of it (comment/preamble lines break strict parsers)

Test IDs: [EXPORT_CITE_001] through [EXPORT_CITE_006]
"""

from pathlib import Path

# Repo root from tests/unit/services/evaluation/ -> up 4 levels
_REPO_ROOT = Path(__file__).resolve().parents[4]


# =============================================================================
# Helpers
# =============================================================================

def _create_scenario(db, name='Citation Scenario', ftype_id=4):
    """Minimal comparison scenario — the citation block is unconditional, so no
    items/votes are needed to exercise the envelope."""
    from db.models.scenario import FeatureFunctionType, RatingScenarios

    if not FeatureFunctionType.query.get(ftype_id):
        db.session.add(FeatureFunctionType(function_type_id=ftype_id, name='comparison'))
        db.session.flush()

    scenario = RatingScenarios(
        scenario_name=name,
        function_type_id=ftype_id,
        config_json={},
        created_by='creator',
    )
    db.session.add(scenario)
    db.session.flush()
    return scenario


# =============================================================================
# Envelope
# =============================================================================

class TestCitationInExportEnvelope:

    def test_EXPORT_CITE_001_collect_results_envelope_has_citation(self, app, db):
        from services.evaluation import results_export_service as export

        scenario = _create_scenario(db)
        db.session.commit()

        result = export.collect_results(scenario, include_llms=False)

        assert 'citation' in result, 'JSON export envelope must carry the citation block'
        citation = result['citation']
        # doi/url kamen mit der Proceedings-Version dazu: der Prosa-String in
        # 'paper' ist fuer Menschen, diese beiden sind maschinenlesbar.
        assert set(citation) == {'message', 'paper', 'doi', 'url', 'bibtex_url'}
        assert citation['message'] == (
            'If you use data produced with LLARS in academic work, '
            'please cite the LLARS paper.'
        )
        # Die publizierte Fassung, nicht mehr der Preprint: wer einen Export
        # zitiert, soll die Proceedings-Version nennen.
        assert 'doi:10.24963/ijcai.2026/995' in citation['paper']
        assert 'IJCAI-26' in citation['paper']
        assert 'arXiv' not in citation['paper']
        assert citation['paper'].startswith('Steigerwald et al. (2026).')
        assert citation['doi'] == '10.24963/ijcai.2026/995'
        assert citation['url'] == 'https://doi.org/10.24963/ijcai.2026/995'
        assert citation['bibtex_url'] == (
            'https://github.com/th-nuernberg/llars/blob/main/CITATION.cff'
        )

    def test_EXPORT_CITE_002_citation_block_is_a_defensive_copy(self):
        """A downstream mutation of one export's block must not leak into the
        module-level constant (the worker process is long-lived)."""
        from services.evaluation.results_export_service import (
            CITATION_BLOCK,
            citation_block,
        )

        block = citation_block()
        assert block == CITATION_BLOCK
        assert block is not CITATION_BLOCK

        block['message'] = 'mutated'
        assert CITATION_BLOCK['message'] != 'mutated'
        assert citation_block()['message'] != 'mutated'


# =============================================================================
# Route envelopes (source-level guards)
# =============================================================================

class TestCitationInRouteEnvelopes:
    """Both routes build their JSON envelope from an explicit key list, so a
    new envelope field is silently dropped unless it is wired in by hand.
    Source-level assertions mirror APIV1_RES_013, which guards the same
    regression for `timing_metrics`."""

    def test_EXPORT_CITE_003_v1_json_envelope_forwards_citation(self):
        src = _REPO_ROOT / 'app' / 'routes' / 'api_v1' / 'scenario_results_routes.py'
        body = src.read_text(encoding='utf-8')
        assert '"citation": citation_block()' in body, (
            'v1 JSON envelope must include the citation block'
        )

    def test_EXPORT_CITE_004_gui_json_envelope_forwards_citation(self):
        src = _REPO_ROOT / 'app' / 'routes' / 'scenarios' / 'scenario_manager_api.py'
        body = src.read_text(encoding='utf-8')
        assert "'citation': citation_block()" in body, (
            'GUI JSON export envelope must include the citation block'
        )

    def test_EXPORT_CITE_005_single_source_of_truth(self):
        """The literal lives in exactly one place — both routes import it."""
        for rel in (
            ('app', 'routes', 'api_v1', 'scenario_results_routes.py'),
            ('app', 'routes', 'scenarios', 'scenario_manager_api.py'),
        ):
            body = (_REPO_ROOT.joinpath(*rel)).read_text(encoding='utf-8')
            assert 'citation_block' in body
            # No copy-pasted literal outside results_export_service
            assert 'If you use data produced with LLARS' not in body, (
                f'{rel[-1]} must reference citation_block(), not inline the text'
            )


# =============================================================================
# CSV / JSONL must stay machine-parseable
# =============================================================================

class TestCitationNotInFlatFormats:

    def test_EXPORT_CITE_006_citation_is_not_a_csv_column(self):
        """A `citation` column (or a comment preamble) would break strict CSV
        consumers such as pandas.read_csv / R read.csv."""
        from services.evaluation.results_export_service import ROW_COLUMNS

        assert 'citation' not in ROW_COLUMNS
        assert not any(c.startswith('citation') for c in ROW_COLUMNS)
