"""
Synthetic training data generator + LightGBM model trainer.

Strategy:
- Generate 800 (candidate, job) pairs with random realistic features
- Label each pair with a domain-expert ground-truth formula that captures
  non-linear interactions (e.g., both skill match AND capability must be high)
- Train LightGBM regressor; the model learns weights that may outperform
  any hand-tuned linear formula
- Save model to ml/ranker_model.pkl
"""
import pickle
import random
import numpy as np
from pathlib import Path

from ml.features import FEATURE_NAMES


def _generate_sample() -> tuple[np.ndarray, float]:
    """Returns (feature_vector, relevance_score_0_to_100)."""
    semantic = random.uniform(20, 100)
    capability = random.uniform(20, 100)
    matched_req_pct = random.uniform(0, 100)
    matched_pref_pct = random.uniform(0, 100)
    verification = random.uniform(30, 100)
    learning = random.uniform(20, 100)
    growth = random.uniform(20, 100)
    career = random.uniform(0, 100)
    project = random.uniform(0, 100)
    evidence = random.uniform(0, 100)
    skill_gap_pct = 100 - matched_req_pct + random.uniform(-5, 5)
    skill_gap_pct = max(0, min(100, skill_gap_pct))
    experience_gap = random.uniform(0, 5)
    cert_gap = random.choice([0, 0, 0, 1, 1, 2])
    exp_years = random.uniform(0, 12)
    cert_count = random.choice([0, 0, 1, 1, 2, 3])

    features = np.array([
        semantic, capability, matched_req_pct, matched_pref_pct,
        verification, learning, growth, career, project, evidence,
        skill_gap_pct, experience_gap, cert_gap, exp_years, cert_count,
    ], dtype=np.float32)

    # Ground-truth label: captures multiplicative interactions
    # A great candidate needs BOTH match AND capability (not just one)
    match_capability_synergy = (matched_req_pct / 100) * (capability / 100) * 40
    semantic_contribution = semantic * 0.15
    growth_contribution = ((growth + learning) / 2) * 0.10
    verification_contribution = verification * 0.10
    gap_penalty = skill_gap_pct * 0.12 + experience_gap * 3 + cert_gap * 2
    exp_bonus = min(exp_years * 1.5, 10)

    raw = (match_capability_synergy + semantic_contribution +
           growth_contribution + verification_contribution +
           exp_bonus - gap_penalty)
    label = max(0.0, min(100.0, raw))
    return features, label


def generate_training_data(n: int = 800) -> tuple[np.ndarray, np.ndarray]:
    random.seed(42)
    np.random.seed(42)
    X, y = [], []
    for _ in range(n):
        feat, label = _generate_sample()
        X.append(feat)
        y.append(label)
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def train_and_save(model_path: Path) -> None:
    try:
        import lightgbm as lgb
        from sklearn.model_selection import cross_val_score
    except ImportError:
        print("[trainer] lightgbm or scikit-learn not installed — skipping ML training.")
        return

    print("[trainer] Generating synthetic training data...")
    X, y = generate_training_data(1000)

    model = lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        min_child_samples=10,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        verbose=-1,
    )

    scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    print(f"[trainer] 5-fold CV R² = {scores.mean():.4f} ± {scores.std():.4f}")

    model.fit(X, y)

    importances = sorted(
        zip(FEATURE_NAMES, model.feature_importances_),
        key=lambda x: x[1], reverse=True,
    )
    print("[trainer] Top feature importances:")
    for name, imp in importances[:8]:
        print(f"  {name:30s} {imp:.0f}")

    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"[trainer] Model saved to {model_path}")
