"""
ML-powered ranker.

On first use it trains a LightGBM model (takes ~3 seconds).
Falls back to a weighted formula if LightGBM is not installed.
"""
import pickle
from pathlib import Path

import numpy as np

from config import MODEL_PATH
from ml.features import FeatureVector, to_numpy

_model = None
_use_formula = False


def _formula_score(fv: FeatureVector) -> float:
    """
    Enhanced weighted formula (noel's formula + poojit sub-scores + gap penalty).
    Used as fallback when LightGBM is unavailable.
    """
    score = (
        fv.semantic_match_score * 0.25
        + fv.capability_score * 0.20
        + fv.matched_req_pct * 0.15
        + fv.verification_score * 0.10
        + fv.growth_score * 0.10
        + fv.learning_score * 0.05
        + fv.evidence_score * 0.05
        - fv.skill_gap_pct * 0.10
        - fv.experience_gap * 3.0
        - fv.cert_gap * 2.0
    )
    return max(0.0, min(100.0, round(score, 2)))


def _load_or_train() -> None:
    global _model, _use_formula

    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
        print(f"[ranker] Loaded model from {MODEL_PATH}")
        return

    try:
        from ml.trainer import train_and_save
        train_and_save(MODEL_PATH)
        if MODEL_PATH.exists():
            with open(MODEL_PATH, "rb") as f:
                _model = pickle.load(f)
        else:
            _use_formula = True
    except Exception as e:
        print(f"[ranker] ML training failed ({e}), using formula fallback.")
        _use_formula = True


def predict(fv: FeatureVector) -> float:
    global _model, _use_formula
    if _model is None and not _use_formula:
        _load_or_train()

    if _use_formula or _model is None:
        return _formula_score(fv)

    x = to_numpy(fv).reshape(1, -1)
    raw = float(_model.predict(x)[0])
    return max(0.0, min(100.0, round(raw, 2)))
