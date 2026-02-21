# anonymize_paths.py
"""
Path configuration for anonymize service resources.
"""

from __future__ import annotations

import os
from pathlib import Path

from .anonymize_constants import _get_resource_base_dir


def get_paths() -> dict[str, Path]:
    """Get all paths for anonymize service resources."""
    base = _get_resource_base_dir()
    model_dir = Path(os.environ.get("ANONYMIZE_MODEL_DIR", str(base / "models" / "anonymize")))
    data_dir = Path(os.environ.get("ANONYMIZE_DATA_DIR", str(base / "data" / "anonymize")))

    ner_dir = model_dir / "ner-german-large"
    ner_model_file = (
        ner_dir
        / "6b8de9edd73722050be2547acf64c037b2df833c6e8f0e88934de08385e26c1e.4b0797effcc6ebb1889d5d29784b97f0a099c1569b319d87d7c387e44e2bba48"
    )

    recommender_dir = model_dir / "recommender_system"
    return {
        "base": base,
        "model_dir": model_dir,
        "data_dir": data_dir,
        "db": data_dir / "pseudonymize.db",
        "ner_dir": ner_dir,
        "ner_model": ner_model_file,
        "recommender": recommender_dir / "MuncipalityRecommender.sav",
        "scaler": recommender_dir / "Scaler.sav",
    }
