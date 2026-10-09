"""Arma el reporte de drift: qué features cambiaron y si hay que alertar."""
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

import pandas as pd

from commons.config import DatasetConfig, DriftConfig
from process_drift.metrics import CATEGORICAL_METRICS, NUMERIC_METRICS


@dataclass
class FeatureDrift:
    feature: str
    kind: str          # numeric | categorical
    algorithm: str
    score: float
    threshold: float
    drifted: bool


@dataclass
class DriftResult:
    name: str
    type: str
    alert: bool
    share_drifted: float
    drifted_features: List[str]
    features: List[FeatureDrift] = field(default_factory=list)


def _feature_drift(name: str, kind: str, algorithm: str, score: float, threshold: float) -> FeatureDrift:
    return FeatureDrift(
        feature=name, kind=kind, algorithm=algorithm,
        score=round(score, 4), threshold=threshold, drifted=score >= threshold,
    )


def compute_input_drift(
    baseline: pd.DataFrame, current: pd.DataFrame, ds: DatasetConfig, cfg: DriftConfig
) -> DriftResult:
    """Compara cada feature de entrada entre entrenamiento y producción."""
    results: List[FeatureDrift] = []
    num_metric = NUMERIC_METRICS[cfg.numeric_algorithm]
    cat_metric = CATEGORICAL_METRICS[cfg.categorical_algorithm]

    for col in ds.numeric_features:
        score = num_metric(baseline[col], current[col])
        results.append(_feature_drift(col, "numeric", cfg.numeric_algorithm, score, cfg.threshold))
    for col in ds.categorical_features:
        score = cat_metric(baseline[col].astype(str), current[col].astype(str))
        results.append(_feature_drift(col, "categorical", cfg.categorical_algorithm, score, cfg.threshold))

    drifted = [r.feature for r in results if r.drifted]
    share = len(drifted) / len(results) if results else 0.0
    return DriftResult(
        name=cfg.name, type=cfg.type, alert=share >= cfg.alert_share and bool(drifted),
        share_drifted=round(share, 4), drifted_features=drifted, features=results,
    )


def compute_output_drift(
    baseline_scores: "pd.Series[Any]", current_scores: "pd.Series[Any]", cfg: DriftConfig
) -> DriftResult:
    """Compara la distribución de scores del modelo: ¿está prediciendo distinto que antes?"""
    score = NUMERIC_METRICS[cfg.numeric_algorithm](baseline_scores, current_scores)
    result = _feature_drift("score", "numeric", cfg.numeric_algorithm, score, cfg.threshold)
    return DriftResult(
        name=cfg.name, type=cfg.type, alert=result.drifted,
        share_drifted=1.0 if result.drifted else 0.0,
        drifted_features=["score"] if result.drifted else [], features=[result],
    )


def build_report(
    model_name: str, date: str, scenario: str, rows: int,
    results: List[DriftResult], score_summary: Dict[str, float],
) -> Dict[str, Any]:
    return {
        "model_name": model_name,
        "date": date,
        "scenario": scenario,
        "rows": rows,
        "alert": any(r.alert for r in results),
        "score_summary": score_summary,
        "drifts": [asdict(r) for r in results],
    }
