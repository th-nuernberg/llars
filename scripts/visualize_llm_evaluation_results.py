#!/usr/bin/env python3
"""Build an interactive dashboard for LLARS LLM evaluation exports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


BUCKET_ORDER = ["gut", "mittel", "neutral", "schlecht"]
BUCKET_SCORE = {"gut": 3.0, "mittel": 2.0, "neutral": 1.0, "schlecht": 0.0}
BUCKET_COLORS = {
    "gut": "#1b9e77",
    "mittel": "#d95f02",
    "neutral": "#7570b3",
    "schlecht": "#e7298a",
}


def short_model_name(model_id: str) -> str:
    if not isinstance(model_id, str):
        return str(model_id)
    tail = model_id.split(":")[-1]
    if "/" in tail:
        return tail.split("/")[-1]
    if "/" in model_id:
        return model_id.split("/")[-1]
    return tail


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a high-quality visualization dashboard for an LLARS evaluation export."
    )
    parser.add_argument("--export-dir", required=True, help="Directory with exported TSV files.")
    parser.add_argument(
        "--results-file",
        default="scenario_139_results.tsv",
        help="Results TSV containing payload_json bucket assignments.",
    )
    parser.add_argument(
        "--outputs-file",
        default="generated_outputs_job_72.tsv",
        help="TSV with generated_output ID to llm_model_name mapping.",
    )
    parser.add_argument(
        "--config-file",
        default="scenario_139_config.tsv",
        help="Scenario config TSV including config_json.",
    )
    parser.add_argument(
        "--summary-file",
        default="scenario_139_summary.tsv",
        help="Scenario summary TSV.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory. Defaults to <export-dir>/visualizations.",
    )
    parser.add_argument(
        "--title",
        default="LLARS Evaluation Dashboard",
        help="Dashboard title.",
    )
    return parser.parse_args()


def load_inputs(
    export_dir: Path,
    results_file: str,
    outputs_file: str,
    config_file: str,
    summary_file: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    results_df = pd.read_csv(export_dir / results_file, sep="\t")
    outputs_df = pd.read_csv(export_dir / outputs_file, sep="\t")
    config_df = pd.read_csv(export_dir / config_file, sep="\t")
    summary_df = pd.read_csv(export_dir / summary_file, sep="\t")
    return results_df, outputs_df, config_df, summary_df


def infer_output_id_offset(payload_ids: set[int], output_ids: set[int]) -> int:
    if not payload_ids or not output_ids:
        return 0

    direct_hits = len(payload_ids & output_ids)
    direct_ratio = direct_hits / len(payload_ids)

    if direct_ratio >= 0.9:
        return 0

    offset_min = min(payload_ids) - min(output_ids)
    offset_max = max(payload_ids) - max(output_ids)
    if offset_min != offset_max:
        return 0

    shifted_ids = {pid - offset_min for pid in payload_ids}
    shifted_hits = len(shifted_ids & output_ids)
    shifted_ratio = shifted_hits / len(payload_ids)
    if shifted_ratio > direct_ratio:
        return offset_min
    return 0


def build_judgment_long_df(
    results_df: pd.DataFrame, outputs_df: pd.DataFrame
) -> tuple[pd.DataFrame, int, int]:
    outputs_df = outputs_df.copy()
    outputs_df["output_id"] = pd.to_numeric(outputs_df["output_id"], errors="coerce")
    outputs_df = outputs_df.dropna(subset=["output_id"])
    outputs_df["output_id"] = outputs_df["output_id"].astype(int)
    output_to_model = outputs_df.set_index("output_id")["llm_model_name"].to_dict()

    raw_rows: list[dict[str, object]] = []
    payload_ids: set[int] = set()

    for row in results_df.itertuples(index=False):
        payload_str = getattr(row, "payload_json", None)
        if not isinstance(payload_str, str) or not payload_str.strip():
            continue
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            continue

        evaluator_model = getattr(row, "model_id")
        item_id = getattr(row, "item_id")
        result_id = getattr(row, "id")

        for bucket_name, output_ids in payload.items():
            if bucket_name not in BUCKET_SCORE or not isinstance(output_ids, list):
                continue
            for output_id in output_ids:
                try:
                    output_id_int = int(output_id)
                except (TypeError, ValueError):
                    continue
                raw_rows.append(
                    {
                        "result_id": int(result_id),
                        "item_id": int(item_id),
                        "evaluator_model": evaluator_model,
                        "bucket": bucket_name,
                        "score": BUCKET_SCORE[bucket_name],
                        "payload_output_id": output_id_int,
                    }
                )
                payload_ids.add(output_id_int)

    output_ids = set(output_to_model.keys())
    inferred_offset = infer_output_id_offset(payload_ids, output_ids)

    rows: list[dict[str, object]] = []
    missing_output_refs = 0
    for raw_row in raw_rows:
        lookup_output_id = int(raw_row["payload_output_id"]) - inferred_offset
        candidate_model = output_to_model.get(lookup_output_id)
        if not candidate_model:
            missing_output_refs += 1
            continue
        rows.append(
            {
                "result_id": int(raw_row["result_id"]),
                "item_id": int(raw_row["item_id"]),
                "evaluator_model": raw_row["evaluator_model"],
                "candidate_model": candidate_model,
                "bucket": raw_row["bucket"],
                "score": float(raw_row["score"]),
                "payload_output_id": int(raw_row["payload_output_id"]),
                "mapped_output_id": lookup_output_id,
            }
        )

    long_df = pd.DataFrame(rows)
    if long_df.empty:
        raise RuntimeError("No parseable judgments found. Check input TSV files.")

    long_df["evaluator_short"] = long_df["evaluator_model"].map(short_model_name)
    long_df["candidate_short"] = long_df["candidate_model"].map(short_model_name)
    return long_df, missing_output_refs, inferred_offset


def build_coverage_df(results_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    expected_items = int(results_df["item_id"].nunique())
    coverage_df = (
        results_df.groupby("model_id", as_index=False)["item_id"]
        .nunique()
        .rename(columns={"model_id": "evaluator_model", "item_id": "rated_items"})
    )
    coverage_df["expected_items"] = expected_items
    coverage_df["completion_pct"] = (coverage_df["rated_items"] / expected_items) * 100.0
    coverage_df["evaluator_short"] = coverage_df["evaluator_model"].map(short_model_name)
    coverage_df = coverage_df.sort_values(["rated_items", "evaluator_model"], ascending=[False, True])
    return coverage_df, expected_items


def build_bucket_distribution_df(long_df: pd.DataFrame, evaluator_order: list[str]) -> pd.DataFrame:
    bucket_df = (
        long_df.groupby(["evaluator_model", "bucket"], as_index=False)
        .size()
        .rename(columns={"size": "bucket_count"})
    )
    idx = pd.MultiIndex.from_product(
        [evaluator_order, BUCKET_ORDER], names=["evaluator_model", "bucket"]
    )
    bucket_df = (
        bucket_df.set_index(["evaluator_model", "bucket"]).reindex(idx, fill_value=0).reset_index()
    )
    total_per_eval = bucket_df.groupby("evaluator_model")["bucket_count"].transform("sum")
    bucket_df["bucket_share_pct"] = np.where(
        total_per_eval > 0, (bucket_df["bucket_count"] / total_per_eval) * 100.0, 0.0
    )
    bucket_df["evaluator_short"] = bucket_df["evaluator_model"].map(short_model_name)
    return bucket_df


def build_candidate_score_df(long_df: pd.DataFrame) -> pd.DataFrame:
    candidate_df = (
        long_df.groupby("candidate_model", as_index=False)
        .agg(
            mean_score=("score", "mean"),
            score_std=("score", "std"),
            judgments=("score", "size"),
            unique_items=("item_id", "nunique"),
        )
        .sort_values(["mean_score", "judgments"], ascending=[False, False])
    )
    candidate_df["normalized_quality_pct"] = (candidate_df["mean_score"] / 3.0) * 100.0
    candidate_df["candidate_short"] = candidate_df["candidate_model"].map(short_model_name)
    candidate_df["score_std"] = candidate_df["score_std"].fillna(0.0)
    return candidate_df


def build_eval_candidate_heatmap_df(
    long_df: pd.DataFrame, evaluator_order: list[str], candidate_order: list[str]
) -> pd.DataFrame:
    heat_df = (
        long_df.groupby(["evaluator_model", "candidate_model"], as_index=False)["score"]
        .mean()
        .rename(columns={"score": "mean_score"})
    )
    matrix = heat_df.pivot(
        index="evaluator_model", columns="candidate_model", values="mean_score"
    ).reindex(index=evaluator_order, columns=candidate_order)
    return matrix


def build_pairwise_win_rate_matrix(long_df: pd.DataFrame, candidate_order: list[str]) -> pd.DataFrame:
    wins = pd.DataFrame(
        0, index=candidate_order, columns=candidate_order, dtype=np.int64
    )

    grouped = long_df.groupby(["evaluator_model", "item_id"], sort=False)
    for _, group in grouped:
        candidate_scores = (
            group.groupby("candidate_model", as_index=False)["score"].mean().to_dict("records")
        )
        for pair in combinations(candidate_scores, 2):
            left = pair[0]
            right = pair[1]
            if left["score"] > right["score"]:
                wins.loc[left["candidate_model"], right["candidate_model"]] += 1
            elif right["score"] > left["score"]:
                wins.loc[right["candidate_model"], left["candidate_model"]] += 1

    win_rate = pd.DataFrame(np.nan, index=candidate_order, columns=candidate_order)
    for left in candidate_order:
        for right in candidate_order:
            if left == right:
                continue
            left_wins = int(wins.loc[left, right])
            right_wins = int(wins.loc[right, left])
            total = left_wins + right_wins
            if total > 0:
                win_rate.loc[left, right] = left_wins / total
    return win_rate


def build_figures(
    coverage_df: pd.DataFrame,
    expected_items: int,
    bucket_df: pd.DataFrame,
    heatmap_matrix: pd.DataFrame,
    candidate_df: pd.DataFrame,
    pairwise_matrix: pd.DataFrame,
    title: str,
) -> tuple[go.Figure, go.Figure, go.Figure, go.Figure, go.Figure]:
    coverage_fig = px.bar(
        coverage_df,
        x="evaluator_short",
        y="rated_items",
        color="completion_pct",
        color_continuous_scale="Tealgrn",
        text="completion_pct",
        title="Coverage by Evaluator Model",
        labels={"rated_items": "Rated Items", "evaluator_short": "Evaluator"},
    )
    coverage_fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    coverage_fig.add_hline(
        y=expected_items,
        line_dash="dash",
        line_color="#2f4f4f",
        annotation_text=f"Expected items: {expected_items}",
    )
    coverage_fig.update_layout(
        xaxis_tickangle=-35,
        margin=dict(l=40, r=20, t=60, b=110),
        coloraxis_showscale=False,
    )

    bucket_fig = px.bar(
        bucket_df,
        x="evaluator_short",
        y="bucket_share_pct",
        color="bucket",
        category_orders={"bucket": BUCKET_ORDER},
        color_discrete_map=BUCKET_COLORS,
        title="Bucket Usage by Evaluator (share of assignments)",
        labels={"bucket_share_pct": "Share (%)", "evaluator_short": "Evaluator"},
    )
    bucket_fig.update_layout(
        barmode="stack",
        xaxis_tickangle=-35,
        margin=dict(l=40, r=20, t=60, b=110),
        legend_title_text="Bucket",
    )

    heatmap_fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_matrix.values,
            x=[short_model_name(c) for c in heatmap_matrix.columns],
            y=[short_model_name(r) for r in heatmap_matrix.index],
            text=np.round(heatmap_matrix.values, 2),
            texttemplate="%{text}",
            colorscale="RdYlGn",
            zmin=0,
            zmax=3,
            colorbar={"title": "Mean score"},
            hoverongaps=False,
        )
    )
    heatmap_fig.update_layout(
        title="Evaluator vs Candidate Heatmap (mean bucket score)",
        xaxis_title="Candidate Model",
        yaxis_title="Evaluator Model",
        margin=dict(l=40, r=20, t=60, b=120),
    )

    candidate_fig = px.bar(
        candidate_df,
        x="candidate_short",
        y="mean_score",
        error_y="score_std",
        color="normalized_quality_pct",
        color_continuous_scale="Turbo",
        text="mean_score",
        title="Candidate Leaderboard (aggregated across evaluators)",
        labels={"mean_score": "Mean score (0..3)", "candidate_short": "Candidate"},
    )
    candidate_fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    candidate_fig.update_layout(
        xaxis_tickangle=-35,
        margin=dict(l=40, r=20, t=60, b=110),
        coloraxis_showscale=False,
    )

    pairwise_fig = go.Figure(
        data=go.Heatmap(
            z=pairwise_matrix.values,
            x=[short_model_name(c) for c in pairwise_matrix.columns],
            y=[short_model_name(r) for r in pairwise_matrix.index],
            text=np.round(pairwise_matrix.values, 2),
            texttemplate="%{text}",
            colorscale="RdBu",
            zmid=0.5,
            zmin=0,
            zmax=1,
            colorbar={"title": "Win rate"},
            hoverongaps=False,
        )
    )
    pairwise_fig.update_layout(
        title="Pairwise Win-Rate Matrix (row beats column)",
        xaxis_title="Candidate Model",
        yaxis_title="Candidate Model",
        margin=dict(l=40, r=20, t=60, b=120),
    )

    for fig in [coverage_fig, bucket_fig, heatmap_fig, candidate_fig, pairwise_fig]:
        fig.update_layout(template="plotly_white")

    coverage_fig.update_layout(title=f"{title} - Coverage")
    return coverage_fig, bucket_fig, heatmap_fig, candidate_fig, pairwise_fig


def save_tables(
    output_dir: Path,
    coverage_df: pd.DataFrame,
    bucket_df: pd.DataFrame,
    heatmap_matrix: pd.DataFrame,
    candidate_df: pd.DataFrame,
    pairwise_matrix: pd.DataFrame,
) -> None:
    coverage_df.to_csv(output_dir / "coverage_by_evaluator.tsv", sep="\t", index=False)
    bucket_df.to_csv(output_dir / "bucket_distribution_by_evaluator.tsv", sep="\t", index=False)
    heatmap_matrix.to_csv(output_dir / "evaluator_candidate_mean_score_matrix.tsv", sep="\t")
    candidate_df.to_csv(output_dir / "candidate_leaderboard.tsv", sep="\t", index=False)
    pairwise_matrix.to_csv(output_dir / "pairwise_win_rate_matrix.tsv", sep="\t")


def write_dashboard_html(
    output_dir: Path,
    title: str,
    summary_df: pd.DataFrame,
    configured_models: list[str],
    actual_models: list[str],
    missing_models: list[str],
    missing_output_refs: int,
    inferred_output_id_offset: int,
    figures: tuple[go.Figure, go.Figure, go.Figure, go.Figure, go.Figure],
) -> Path:
    scenario_name = str(summary_df["scenario_name"].iloc[0]) if "scenario_name" in summary_df else "Unknown"
    scenario_id = str(summary_df["id"].iloc[0]) if "id" in summary_df else "Unknown"
    result_rows = int(summary_df["result_rows"].iloc[0]) if "result_rows" in summary_df else 0

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_items = [
        f"Scenario: {scenario_name} (id={scenario_id})",
        f"Configured evaluators: {len(configured_models)}",
        f"Evaluators with results: {len(actual_models)}",
        f"Result rows in snapshot: {result_rows}",
        f"Missing configured evaluators in snapshot: {len(missing_models)}",
        f"Inferred payload->output id offset: {inferred_output_id_offset}",
        f"Unresolved output-id references while parsing payloads: {missing_output_refs}",
        f"Generated at: {generated_at}",
    ]

    if missing_models:
        summary_items.append("Missing evaluator model IDs: " + ", ".join(missing_models))

    fig_html = [
        fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False)
        for i, fig in enumerate(figures)
    ]

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      margin: 0;
      padding: 24px;
      background: #f5f7f9;
      color: #0b1d26;
    }}
    h1 {{
      margin: 0 0 8px 0;
      font-size: 32px;
    }}
    .summary {{
      background: #ffffff;
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 20px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    }}
    .summary ul {{
      margin: 8px 0 0 0;
      padding-left: 20px;
    }}
    .panel {{
      background: #ffffff;
      border-radius: 12px;
      padding: 10px;
      margin-bottom: 16px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="summary">
    <strong>Snapshot summary</strong>
    <ul>
      {''.join(f'<li>{item}</li>' for item in summary_items)}
    </ul>
  </div>
  <div class="panel">{fig_html[0]}</div>
  <div class="panel">{fig_html[1]}</div>
  <div class="panel">{fig_html[2]}</div>
  <div class="panel">{fig_html[3]}</div>
  <div class="panel">{fig_html[4]}</div>
</body>
</html>
"""
    html_path = output_dir / "evaluation_dashboard.html"
    html_path.write_text(html, encoding="utf-8")
    return html_path


def main() -> None:
    args = parse_args()
    export_dir = Path(args.export_dir).resolve()
    output_dir = (
        Path(args.output_dir).resolve() if args.output_dir else (export_dir / "visualizations")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    results_df, outputs_df, config_df, summary_df = load_inputs(
        export_dir=export_dir,
        results_file=args.results_file,
        outputs_file=args.outputs_file,
        config_file=args.config_file,
        summary_file=args.summary_file,
    )

    long_df, missing_output_refs, inferred_output_id_offset = build_judgment_long_df(
        results_df, outputs_df
    )
    coverage_df, expected_items = build_coverage_df(results_df)
    evaluator_order = coverage_df["evaluator_model"].tolist()

    bucket_df = build_bucket_distribution_df(long_df, evaluator_order)
    candidate_df = build_candidate_score_df(long_df)
    candidate_order = candidate_df["candidate_model"].tolist()
    heatmap_matrix = build_eval_candidate_heatmap_df(long_df, evaluator_order, candidate_order)
    pairwise_matrix = build_pairwise_win_rate_matrix(long_df, candidate_order)

    config_json = {}
    if "config_json" in config_df.columns and not config_df.empty:
        try:
            config_json = json.loads(config_df["config_json"].iloc[0])
        except (TypeError, json.JSONDecodeError):
            config_json = {}

    configured_models = config_json.get("llm_evaluators", [])
    actual_models = sorted(results_df["model_id"].dropna().unique().tolist())
    missing_models = sorted(set(configured_models) - set(actual_models))

    figures = build_figures(
        coverage_df=coverage_df,
        expected_items=expected_items,
        bucket_df=bucket_df,
        heatmap_matrix=heatmap_matrix,
        candidate_df=candidate_df,
        pairwise_matrix=pairwise_matrix,
        title=args.title,
    )
    save_tables(
        output_dir=output_dir,
        coverage_df=coverage_df,
        bucket_df=bucket_df,
        heatmap_matrix=heatmap_matrix,
        candidate_df=candidate_df,
        pairwise_matrix=pairwise_matrix,
    )
    html_path = write_dashboard_html(
        output_dir=output_dir,
        title=args.title,
        summary_df=summary_df,
        configured_models=configured_models,
        actual_models=actual_models,
        missing_models=missing_models,
        missing_output_refs=missing_output_refs,
        inferred_output_id_offset=inferred_output_id_offset,
        figures=figures,
    )

    print(f"Dashboard written to: {html_path}")
    print(f"Aggregated TSV files written to: {output_dir}")
    print(f"Rows parsed into long format: {len(long_df)}")
    print(f"Configured evaluators: {len(configured_models)}")
    print(f"Evaluators with results: {len(actual_models)}")
    print(f"Missing configured evaluators in snapshot: {len(missing_models)}")
    print(f"Inferred payload->output ID offset: {inferred_output_id_offset}")
    print(f"Expected items per evaluator: {expected_items}")


if __name__ == "__main__":
    main()
