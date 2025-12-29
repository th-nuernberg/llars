#!/usr/bin/env python3
"""
Test different German/multilingual cross-encoder models for RAG reranking.
Compare speed and quality.
"""

import os
import sys
import time

sys.path.insert(0, '/app')
os.chdir('/app')

from sentence_transformers import CrossEncoder
import numpy as np

# Test queries
QUERIES = [
    ("Welche Kurse bietet Kathrin an?", "tanzmitkathrin"),
    ("Wer ist alles im Team?", "bewabeck"),
]

# German/multilingual cross-encoder models to test
# Format: (model_id, display_name, description)
MODELS = [
    # Current best - German specific (largest)
    ("svalabs/cross-electra-ms-marco-german-uncased",
     "German ELECTRA (Large)",
     "Bestes deutsches Modell, höchste Qualität, mehr Ressourcen"),

    # German DistilBERT - smaller, faster
    ("ML6team/cross-encoder-mmarco-german-distilbert-base",
     "German DistilBERT (Medium)",
     "Gute deutsche Qualität, schneller als ELECTRA"),

    # Multilingual mMARCO - balanced
    ("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
     "Multilingual MiniLM (Medium)",
     "Multilingual, gute Balance zwischen Geschwindigkeit und Qualität"),

    # Smaller/faster multilingual
    ("cross-encoder/mmarco-mMiniLMv2-L6-H384-v1",
     "Multilingual MiniLM-L6 (Small)",
     "Schnellstes multilinguales Modell, geringere Qualität"),

    # English baseline for comparison
    ("cross-encoder/ms-marco-MiniLM-L-6-v2",
     "English MiniLM-L6 (Small)",
     "Schnellstes Modell, nur für Englisch optimiert"),
]

# Sample documents to test
TEST_DOCS = [
    # tanzmitkathrin - relevant for "Kurse"
    {"title": "Home - Tanz mit Kathrin", "content": """
Tanz mit Kathrin | Twerk, Tease & Fitness in Aschaffenburg und Online
Willkommen bei Tanz mit Kathrin! Hier findest du Kurse für Twerk, Tease und Fitness.
Kathrin bietet verschiedene Kurse an: Tease-Kurse für deine sinnliche Seite,
Twerk-Kurse als Fullbody-Workout mit Spaßfaktor. Die Kurse sind für alle ab 18 Jahren.
Levels von Newbies bis Intermediate verfügbar.
"""},
    # tanzmitkathrin - irrelevant (Datenschutz with nav menu)
    {"title": "Datenschutz - Tanz mit Kathrin", "content": """
Datenschutzerklärung | Tanz mit Kathrin
HOME ÜBER MICH KURSE ANGEBOTE KONTAKT
Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren
personenbezogenen Daten passiert, wenn Sie diese Website besuchen.
"""},
    # bewabeck - relevant for "Team"
    {"title": "Team - Beck Bauplanungs GmbH", "content": """
Team – Beck Bauplanungs GmbH
Beck Bauplanungs GmbH Team
Walter Beck - Firmengründer / Geschäftsführer
Michael Frisch - Geschäftsführer
Elisa Klein - Sonderaufgaben
"""},
    # bewabeck - irrelevant
    {"title": "Thilo Schulze - Beck Bauplanungs", "content": """
Thilo Schulze – Beck Bauplanungs GmbH
Artikel von: Thilo Schulze
Nothing Found - It seems we can't find what you're looking for.
"""},
]


def test_model(model_id, display_name, description):
    """Test a single model for speed and relevance."""
    print(f"\n{'='*70}")
    print(f"Testing: {display_name}")
    print(f"Model: {model_id}")
    print(f"Description: {description}")
    print('='*70)

    # Load model and measure time
    load_start = time.time()
    try:
        model = CrossEncoder(model_id, max_length=512)
    except Exception as e:
        print(f"  ERROR loading: {e}")
        return None
    load_time = time.time() - load_start
    print(f"  Load time: {load_time:.2f}s")

    results = {
        "model_id": model_id,
        "display_name": display_name,
        "description": description,
        "load_time": load_time,
        "queries": []
    }

    for query, context in QUERIES:
        print(f"\n  Query: '{query}'")

        # Create pairs
        pairs = [(query, doc["content"]) for doc in TEST_DOCS]

        # Measure inference time
        infer_start = time.time()
        scores = model.predict(pairs)
        infer_time = time.time() - infer_start

        # Sort and display results
        scored_docs = list(zip(TEST_DOCS, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        print(f"    Inference time: {infer_time*1000:.1f}ms")
        print(f"    Results:")
        for i, (doc, score) in enumerate(scored_docs):
            relevant = "✓" if context in doc["title"].lower().replace(" ", "") else " "
            print(f"      {i+1}. [{relevant}] {score:+.3f} | {doc['title'][:40]}")

        # Check if relevant doc is #1
        top_doc = scored_docs[0][0]
        is_correct = context in top_doc["title"].lower().replace(" ", "")

        results["queries"].append({
            "query": query,
            "infer_time_ms": infer_time * 1000,
            "correct": is_correct,
            "top_score": float(scored_docs[0][1]),
            "second_score": float(scored_docs[1][1]),
        })

    return results


def main():
    print("="*70)
    print("CROSS-ENCODER RERANKER COMPARISON")
    print("Testing speed and quality for German queries")
    print("="*70)

    all_results = []

    for model_id, display_name, description in MODELS:
        result = test_model(model_id, display_name, description)
        if result:
            all_results.append(result)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"{'Model':<35} {'Load':<8} {'Infer':<10} {'Correct':<8} {'Quality'}")
    print("-"*75)

    for r in all_results:
        avg_infer = np.mean([q["infer_time_ms"] for q in r["queries"]])
        correct = sum(1 for q in r["queries"] if q["correct"])
        total = len(r["queries"])
        avg_margin = np.mean([q["top_score"] - q["second_score"] for q in r["queries"]])

        print(f"{r['display_name'][:33]:<35} {r['load_time']:.1f}s    {avg_infer:.0f}ms      {correct}/{total}      {avg_margin:+.2f}")

    print("\n" + "="*70)
    print("RECOMMENDATIONS FOR CHATBOT SETTINGS")
    print("="*70)
    print("""
1. German ELECTRA (Large)     - Beste Qualität für Deutsch, aber langsamer
2. German DistilBERT (Medium) - Gute Balance für deutsche Inhalte
3. Multilingual MiniLM (Med)  - Für gemischte Sprachen
4. Multilingual MiniLM-L6     - Schnellste Option mit akzeptabler Qualität
""")


if __name__ == "__main__":
    main()
