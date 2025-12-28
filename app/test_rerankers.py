#!/usr/bin/env python3
"""
Test different German/multilingual cross-encoder models for RAG reranking.
"""

import os
import sys

# Set up path
sys.path.insert(0, '/app')
os.chdir('/app')

from sentence_transformers import CrossEncoder
import numpy as np

# Test query
QUERY = "Wer ist alles im Team?"
TARGET_DOC_ID = 631  # Team page
COLLECTION_ID = 3    # bewabeck collection

# German/multilingual cross-encoder models to test (verified on HuggingFace)
MODELS = [
    # Current model
    ("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1", "mMARCO Mini (current)"),

    # Other multilingual mMARCO
    ("cross-encoder/mmarco-mdeberta-v3-base-5epochs-v1", "mMARCO mDeBERTa"),

    # German-specific models
    ("svalabs/cross-electra-ms-marco-german-uncased", "German ELECTRA"),
    ("ML6team/cross-encoder-mmarco-german-distilbert-base", "German DistilBERT"),

    # Original English (for comparison)
    ("cross-encoder/ms-marco-MiniLM-L-6-v2", "English MiniLM (original)"),
    ("cross-encoder/ms-marco-MiniLM-L-12-v2", "English MiniLM L12"),
]

def get_test_candidates():
    """Get actual candidates from database."""
    import pymysql

    conn = pymysql.connect(
        host='llars_db_service',
        user='dev_user',
        password='dev_password_change_me',
        database='database_llars',
        charset='utf8mb4'
    )

    cursor = conn.cursor()

    # Get chunks from the collection - simulate what vector search would return
    cursor.execute("""
        SELECT c.id, c.content, c.document_id, d.title
        FROM rag_document_chunks c
        JOIN rag_documents d ON c.document_id = d.id
        WHERE d.collection_id = %s
        AND c.content IS NOT NULL
        AND LENGTH(c.content) > 50
        ORDER BY RAND(42)
        LIMIT 40
    """, (COLLECTION_ID,))

    rows = cursor.fetchall()

    candidates = []
    for row in rows:
        candidates.append({
            'chunk_id': row[0],
            'content': row[1][:1500] if row[1] else "",
            'document_id': row[2],
            'title': row[3],
        })

    # Make sure Team page is in candidates
    cursor.execute("""
        SELECT c.id, c.content, c.document_id, d.title
        FROM rag_document_chunks c
        JOIN rag_documents d ON c.document_id = d.id
        WHERE d.id = %s
        LIMIT 3
    """, (TARGET_DOC_ID,))

    team_rows = cursor.fetchall()
    team_doc_ids = [c['document_id'] for c in candidates]

    for row in team_rows:
        if row[2] not in team_doc_ids:
            candidates.append({
                'chunk_id': row[0],
                'content': row[1][:1500] if row[1] else "",
                'document_id': row[2],
                'title': row[3],
            })

    conn.close()
    return candidates


def test_model(model_name, display_name, candidates, query):
    """Test a single model with both pure and hybrid scoring."""
    print(f"\n{'='*70}")
    print(f"Testing: {display_name}")
    print(f"Model: {model_name}")
    print('='*70)

    try:
        model = CrossEncoder(model_name, max_length=512)
    except Exception as e:
        print(f"  ERROR loading model: {e}")
        return None

    # Create pairs
    pairs = [(query, c['content']) for c in candidates]

    # Get scores
    try:
        scores = model.predict(pairs)
    except Exception as e:
        print(f"  ERROR predicting: {e}")
        return None

    # Normalize scores to 0-1
    ce_min, ce_max = float(min(scores)), float(max(scores))
    ce_range = ce_max - ce_min if ce_max > ce_min else 1.0
    ce_normalized = [(float(s) - ce_min) / ce_range for s in scores]

    # Simulate original embedding scores
    # Team page would have highest embedding score (~0.46), others lower
    orig_scores = []
    for c in candidates:
        if c['document_id'] == TARGET_DOC_ID:
            orig_scores.append(0.465)  # Team page had highest embedding score
        else:
            orig_scores.append(0.35 + np.random.uniform(0, 0.08))  # Others around 0.35-0.43

    results = []
    for i, c in enumerate(candidates):
        results.append({
            'document_id': c['document_id'],
            'title': c['title'],
            'ce_raw': float(scores[i]),
            'ce_norm': ce_normalized[i],
            'orig': orig_scores[i],
            'pure_ce': ce_normalized[i],
            'hybrid_70': 0.7 * ce_normalized[i] + 0.3 * orig_scores[i],
            'hybrid_60': 0.6 * ce_normalized[i] + 0.4 * orig_scores[i],
            'hybrid_50': 0.5 * ce_normalized[i] + 0.5 * orig_scores[i],
        })

    # Sort by different methods
    pure_sorted = sorted(results, key=lambda x: x['pure_ce'], reverse=True)
    hybrid70_sorted = sorted(results, key=lambda x: x['hybrid_70'], reverse=True)
    hybrid60_sorted = sorted(results, key=lambda x: x['hybrid_60'], reverse=True)
    hybrid50_sorted = sorted(results, key=lambda x: x['hybrid_50'], reverse=True)

    # Find Team page position in each
    def find_team_position(sorted_list):
        for i, r in enumerate(sorted_list):
            if r['document_id'] == TARGET_DOC_ID:
                return i + 1, r
        return -1, None

    pure_pos, pure_r = find_team_position(pure_sorted)
    h70_pos, _ = find_team_position(hybrid70_sorted)
    h60_pos, _ = find_team_position(hybrid60_sorted)
    h50_pos, _ = find_team_position(hybrid50_sorted)

    print(f"\n  Score range: {ce_min:.3f} to {ce_max:.3f}")
    print(f"\n  Team page (doc_id={TARGET_DOC_ID}) rankings:")
    print(f"    Pure CE:     #{pure_pos}")
    print(f"    Hybrid 70%:  #{h70_pos}")
    print(f"    Hybrid 60%:  #{h60_pos}")
    print(f"    Hybrid 50%:  #{h50_pos}")

    print(f"\n  Top 5 with Pure Cross-Encoder:")
    for i, r in enumerate(pure_sorted[:5]):
        marker = " *** TEAM ***" if r['document_id'] == TARGET_DOC_ID else ""
        print(f"    {i+1}. ce={r['ce_raw']:.3f} norm={r['ce_norm']:.3f} | {r['title'][:45]}{marker}")

    print(f"\n  Top 5 with Hybrid 60/40:")
    for i, r in enumerate(hybrid60_sorted[:5]):
        marker = " *** TEAM ***" if r['document_id'] == TARGET_DOC_ID else ""
        print(f"    {i+1}. h60={r['hybrid_60']:.3f} | {r['title'][:45]}{marker}")

    return {
        'model': model_name,
        'display': display_name,
        'pure_position': pure_pos,
        'hybrid70_position': h70_pos,
        'hybrid60_position': h60_pos,
        'hybrid50_position': h50_pos,
        'team_ce_raw': pure_r['ce_raw'] if pure_r else 0,
    }


def main():
    print("="*70)
    print("CROSS-ENCODER RERANKER TEST")
    print(f"Query: '{QUERY}'")
    print(f"Target: Team page (doc_id={TARGET_DOC_ID})")
    print("="*70)

    print("\nFetching test candidates from database...")
    candidates = get_test_candidates()
    print(f"Got {len(candidates)} candidates")

    # Check if Team page is in candidates
    team_chunks = [c for c in candidates if c['document_id'] == TARGET_DOC_ID]
    print(f"Team page chunks in candidates: {len(team_chunks)}")

    if team_chunks:
        print(f"Team page content preview: {team_chunks[0]['content'][:200]}...")

    results = []
    for model_name, display_name in MODELS:
        try:
            result = test_model(model_name, display_name, candidates, QUERY)
            if result:
                results.append(result)
        except Exception as e:
            print(f"Error testing {model_name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY - Team Page Rankings (lower is better)")
    print("="*70)
    print(f"{'Model':<35} {'Pure':<8} {'H70%':<8} {'H60%':<8} {'H50%':<8} {'CE Score':<10}")
    print("-"*85)
    for r in sorted(results, key=lambda x: x['pure_position'] if x['pure_position'] > 0 else 999):
        print(f"{r['display'][:33]:<35} #{r['pure_position']:<6} #{r['hybrid70_position']:<6} #{r['hybrid60_position']:<6} #{r['hybrid50_position']:<6} {r['team_ce_raw']:.3f}")

    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)

    # Find best model
    best_pure = min(results, key=lambda x: x['pure_position'] if x['pure_position'] > 0 else 999)
    best_hybrid = min(results, key=lambda x: x['hybrid60_position'] if x['hybrid60_position'] > 0 else 999)

    print(f"Best with Pure CE:    {best_pure['display']} (position #{best_pure['pure_position']})")
    print(f"Best with Hybrid 60%: {best_hybrid['display']} (position #{best_hybrid['hybrid60_position']})")


if __name__ == "__main__":
    main()
