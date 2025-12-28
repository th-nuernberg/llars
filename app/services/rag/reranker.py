"""
RAG Reranker

Optional reranking step for retrieved chunks.

Modes (env var `RAG_RERANK_MODE`):
- off: keep vector order
- lexical (default): lightweight token overlap rerank
- cross-encoder: sentence-transformers CrossEncoder rerank (requires model download)
"""

from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

from db.models.llm_model import LLMModel

logger = logging.getLogger(__name__)


def rerank_results(
    query: str,
    results: List[Dict[str, Any]],
    *,
    use_cross_encoder: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Rerank search results to improve relevance.

    Args:
        query: The search query
        results: List of search results to rerank
        use_cross_encoder: If True, use cross-encoder reranking. If False, use lexical.
                          If None, falls back to RAG_RERANK_MODE env var.

    Returns:
        Reranked list of results
    """
    # Determine mode: explicit parameter takes precedence over env var
    if use_cross_encoder is True:
        mode = "cross-encoder"
    elif use_cross_encoder is False:
        mode = "lexical"
    else:
        mode = (os.environ.get("RAG_RERANK_MODE") or "lexical").strip().lower()

    if mode in ("off", "false", "0", "disabled", "none"):
        return results

    if mode in ("cross-encoder", "cross_encoder", "ce"):
        model_name = _get_default_reranker_model()
        if not model_name:
            logger.warning("[Reranker] No reranker model configured in llm_models; falling back to lexical")
            return _lexical_rerank(query, results)
        try:
            return _cross_encoder_rerank(query, results, model_name=model_name)
        except Exception as e:
            logger.warning(f"[Reranker] Cross-encoder rerank failed, falling back to lexical: {e}")
            return _lexical_rerank(query, results)

    return _lexical_rerank(query, results)


def _lexical_rerank(query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return results

    alpha = _get_alpha()

    reranked: List[Dict[str, Any]] = []
    for r in results:
        content = r.get("content") or ""
        content_tokens = set(_tokenize(content))
        overlap = len(query_tokens & content_tokens) / max(1, len(query_tokens))

        base_score = float(r.get("score") or 0.0)
        rerank_score = (1 - alpha) * base_score + alpha * overlap

        r2 = dict(r)
        r2["rerank"] = {
            "mode": "lexical",
            "alpha": alpha,
            "overlap": round(float(overlap), 4),
            "score": round(float(rerank_score), 4),
        }
        reranked.append(r2)

    reranked.sort(key=lambda x: (x.get("rerank", {}).get("score") or 0.0), reverse=True)
    return reranked


def _get_alpha() -> float:
    raw = os.environ.get("RAG_RERANK_ALPHA")
    try:
        val = float(raw) if raw is not None else 0.15
        return max(0.0, min(1.0, val))
    except Exception:
        return 0.15


_TOKEN_RE = re.compile(r"[\wäöüÄÖÜß]+", re.UNICODE)


def _tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall((text or "").lower()) if len(t) >= 2]


def _get_default_reranker_model() -> Optional[str]:
    model = LLMModel.get_default_model(model_type=LLMModel.MODEL_TYPE_RERANKER)
    return model.model_id if model else None


@lru_cache(maxsize=1)
def _get_cross_encoder(model_name: str):
    from sentence_transformers import CrossEncoder

    logger.info(f"[Reranker] Loading CrossEncoder model: {model_name}")
    return CrossEncoder(model_name)


def _cross_encoder_rerank(query: str, results: List[Dict[str, Any]], *, model_name: str) -> List[Dict[str, Any]]:
    """
    Rerank results using cross-encoder model.
    Uses pure cross-encoder scoring (works best with German ELECTRA model).
    """
    if not results:
        return results

    model = _get_cross_encoder(model_name)
    pairs = [(query, (r.get("content") or "")) for r in results]

    scores = model.predict(pairs)

    reranked: List[Dict[str, Any]] = []
    for r, s in zip(results, scores):
        r2 = dict(r)
        r2["rerank"] = {
            "mode": "cross-encoder",
            "model": model_name,
            "score": float(s),
            "orig_score": float(r.get("score") or 0.0),
        }
        reranked.append(r2)

    reranked.sort(key=lambda x: (x.get("rerank", {}).get("score") or 0.0), reverse=True)

    # Log top 5 results after reranking
    logger.info(f"[Reranker] Cross-encoder rerank ({model_name.split('/')[-1]}) for: '{query[:50]}...'")
    for i, r in enumerate(reranked[:5]):
        title = r.get('title', 'Unknown')[:40]
        doc_id = r.get('document_id', '?')
        score = r.get('rerank', {}).get('score', 0)
        logger.info(f"[Reranker]   {i+1}. score={score:.3f} | doc={doc_id} {title}")

    return reranked
