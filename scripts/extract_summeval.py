#!/usr/bin/env python3
"""
Extract SummEval data for LLARS Ranking Demo.

Downloads SummEval dataset and extracts 15 source texts with 5 summaries each.
Each summary has human quality ratings (coherence, consistency, fluency, relevance).

Output: JSON file ready for integration into demo_datasets.py
"""

import json
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print("Installing datasets library...")
    import subprocess
    subprocess.run(["pip", "install", "datasets"], check=True)
    from datasets import load_dataset


def extract_summeval_data(num_texts: int = 15, summaries_per_text: int = 5):
    """
    Extract data from SummEval dataset.

    Args:
        num_texts: Number of source texts to extract
        summaries_per_text: Number of summaries per text (ranked by quality)

    Returns:
        List of ranking samples
    """
    print("Loading SummEval dataset from HuggingFace...")

    # Load the mteb/summeval dataset which has the full data
    dataset = load_dataset("mteb/summeval", split="test")

    print(f"Dataset loaded: {len(dataset)} samples")
    print(f"Columns: {dataset.column_names}")

    # Group summaries by source text
    # The dataset has: text (source), machine_summaries (list), relevance_scores (list)
    ranking_samples = []

    for idx, sample in enumerate(dataset):
        if idx >= num_texts:
            break

        source_text = sample.get('text', '')
        machine_summaries = sample.get('machine_summaries', [])

        # Get human scores - these are lists of scores for each summary
        # mteb/summeval has: human_relevance, human_coherence, human_consistency, human_fluency
        relevance_scores = sample.get('human_relevance', sample.get('relevance', []))
        coherence_scores = sample.get('human_coherence', [])
        consistency_scores = sample.get('human_consistency', [])
        fluency_scores = sample.get('human_fluency', [])

        if not machine_summaries:
            print(f"  Sample {idx}: No summaries found, skipping")
            continue

        # Create summary objects with scores
        summaries_with_scores = []
        for i, summary in enumerate(machine_summaries):
            if i >= len(relevance_scores):
                continue

            # Calculate average score across dimensions
            scores = []
            if relevance_scores and i < len(relevance_scores):
                scores.append(relevance_scores[i])
            if coherence_scores and i < len(coherence_scores):
                scores.append(coherence_scores[i])
            if consistency_scores and i < len(consistency_scores):
                scores.append(consistency_scores[i])
            if fluency_scores and i < len(fluency_scores):
                scores.append(fluency_scores[i])

            avg_score = sum(scores) / len(scores) if scores else 0

            summaries_with_scores.append({
                "content": summary,
                "relevance": relevance_scores[i] if relevance_scores and i < len(relevance_scores) else None,
                "coherence": coherence_scores[i] if coherence_scores and i < len(coherence_scores) else None,
                "consistency": consistency_scores[i] if consistency_scores and i < len(consistency_scores) else None,
                "fluency": fluency_scores[i] if fluency_scores and i < len(fluency_scores) else None,
                "avg_score": avg_score
            })

        # Sort by average score and take top/middle/bottom for variety
        summaries_with_scores.sort(key=lambda x: x['avg_score'], reverse=True)

        # Select diverse summaries: best, good, medium, poor, worst
        if len(summaries_with_scores) >= summaries_per_text:
            n = len(summaries_with_scores)
            indices = [
                0,                    # Best
                n // 4,               # Good
                n // 2,               # Medium
                3 * n // 4,           # Poor
                n - 1                 # Worst
            ]
            selected = [summaries_with_scores[i] for i in indices[:summaries_per_text]]
        else:
            selected = summaries_with_scores[:summaries_per_text]

        # Shuffle to avoid giving away the ranking
        import random
        random.seed(idx)  # Reproducible shuffle
        random.shuffle(selected)

        # Assign IDs
        for i, s in enumerate(selected):
            s['id'] = chr(65 + i)  # A, B, C, D, E

        # Truncate source text if too long (for display)
        display_source = source_text[:2000] + "..." if len(source_text) > 2000 else source_text

        ranking_samples.append({
            "subject": f"Summary Ranking: News Article {idx + 1}",
            "source_text": display_source,
            "summaries": selected,
            "task": "Rank these summaries by quality (coherence, relevance, fluency)"
        })

        print(f"  Extracted text {idx + 1}: {len(selected)} summaries")

    return ranking_samples


def format_for_demo_datasets(samples: list) -> str:
    """Format extracted data as Python code for demo_datasets.py"""

    lines = [
        "# =============================================================================",
        "# RANKING SCENARIO SAMPLES - SummEval Dataset",
        "# Source: https://huggingface.co/datasets/mteb/summeval",
        "# Task: Rank multiple summaries of the same news article by quality",
        "# Each summary has human ratings for: coherence, consistency, fluency, relevance",
        "# =============================================================================",
        "",
        "RANKING_SAMPLES = ["
    ]

    for sample in samples:
        lines.append("    {")
        lines.append(f'        "subject": {json.dumps(sample["subject"])},')

        # Format source text with proper escaping
        source = sample["source_text"].replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'        "source_text": """{sample["source_text"]}""",')

        lines.append('        "summaries": [')
        for s in sample["summaries"]:
            content = s["content"].replace('\\', '\\\\').replace('"', '\\"')
            lines.append("            {")
            lines.append(f'                "id": "{s["id"]}",')
            lines.append(f'                "content": """{s["content"]}""",')
            lines.append(f'                "human_scores": {{')
            lines.append(f'                    "relevance": {s["relevance"]},')
            lines.append(f'                    "coherence": {s["coherence"]},')
            lines.append(f'                    "consistency": {s["consistency"]},')
            lines.append(f'                    "fluency": {s["fluency"]},')
            lines.append(f'                    "avg": {s["avg_score"]:.2f}')
            lines.append(f'                }}')
            lines.append("            },")
        lines.append('        ],')
        lines.append(f'        "task": {json.dumps(sample["task"])}')
        lines.append("    },")

    lines.append("]")

    return "\n".join(lines)


def main():
    output_dir = Path(__file__).parent.parent / "app" / "db" / "seeders"

    print("=" * 60)
    print("SummEval Data Extraction for LLARS Ranking Demo")
    print("=" * 60)

    # Extract data
    samples = extract_summeval_data(num_texts=15, summaries_per_text=5)

    print(f"\nExtracted {len(samples)} ranking samples")

    # Save as JSON for inspection
    json_output = output_dir / "summeval_ranking_data.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON to: {json_output}")

    # Save as Python code
    python_output = output_dir / "summeval_ranking_samples.py"
    python_code = format_for_demo_datasets(samples)
    with open(python_output, 'w', encoding='utf-8') as f:
        f.write(python_code)
    print(f"Saved Python code to: {python_output}")

    print("\n" + "=" * 60)
    print("Done! Copy RANKING_SAMPLES from summeval_ranking_samples.py")
    print("into demo_datasets.py to use the real data.")
    print("=" * 60)


if __name__ == "__main__":
    main()
