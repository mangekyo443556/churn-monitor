"""Lógica pura de entrenamiento: sin leer ni escribir archivos.

Separar la lógica (domain) de la entrada/salida (main.py) permite testearla
con DataFrames pequeños, sin S3 ni disco. Es el mismo principio que la
carpeta `domain/` de cada Lambda en pipeline-model-monitor.
"""
from dataclasses import dataclass
from typing import Any, Dict

import numpy as np
import numpy.typing as npt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from commons.config import DatasetConfig

SCORE_COLUMN = "score"


def clean_dataset(raw: pd.DataFrame, ds: DatasetConfig) -> pd.DataFrame:
    """Deja el dataset listo para entrenar.

    - Columnas numéricas -> números (en Telco, TotalCharges trae espacios vacíos).
    - Columnas categóricas -> texto (SeniorCitizen viene como 0/1).
    - Target -> 1 si es la etiqueta positiva, 0 si no.
    """
    missing = [c for c in ds.features + [ds.target] if c not in raw.columns]
    if missing:
        raise ValueError(f"Faltan columnas en el dataset: {missing}")

    df = raw.copy()
    for col in ds.numeric_features:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ds.categorical_features:
        df[col] = df[col].astype(str)
    df = df.dropna(subset=ds.numeric_features).reset_index(drop=True)
    df[ds.target] = (df[ds.target].astype(str) == ds.positive_label).astype(int)
    return df


def build_pipeline(ds: DatasetConfig) -> Pipeline:
    """Preprocesamiento + modelo en un solo objeto, para guardarlo y cargarlo junto."""
    preprocess = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), ds.numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), ds.categorical_features),
        ]
    )
    return Pipeline(steps=[("preprocess", preprocess), ("model", LogisticRegression(max_iter=1000))])


def predict_scores(model: Pipeline, df: pd.DataFrame, ds: DatasetConfig) -> npt.NDArray[np.float64]:
    """Probabilidad de churn (entre 0 y 1) para cada fila."""
    scores: npt.NDArray[np.float64] = model.predict_proba(df[ds.features])[:, 1]
    return scores


@dataclass
class TrainResult:
    model: Pipeline
    baseline: pd.DataFrame   # filas de entrenamiento + su score: la "referencia"
    holdout: pd.DataFrame    # filas que el modelo no vio: materia prima de "producción"
    metrics: Dict[str, Any]


def train(raw: pd.DataFrame, ds: DatasetConfig, seed: int = 42, holdout_size: float = 0.3) -> TrainResult:
    df = clean_dataset(raw, ds)
    train_df, holdout_df = train_test_split(
        df, test_size=holdout_size, random_state=seed, stratify=df[ds.target]
    )

    model = build_pipeline(ds)
    model.fit(train_df[ds.features], train_df[ds.target])

    holdout_scores = predict_scores(model, holdout_df, ds)
    metrics = {
        "auc_holdout": round(float(roc_auc_score(holdout_df[ds.target], holdout_scores)), 4),
        "accuracy_holdout": round(float(accuracy_score(holdout_df[ds.target], holdout_scores >= 0.5)), 4),
        "rows_train": int(len(train_df)),
        "rows_holdout": int(len(holdout_df)),
        "churn_rate_train": round(float(train_df[ds.target].mean()), 4),
    }

    baseline = train_df.reset_index(drop=True).copy()
    baseline[SCORE_COLUMN] = predict_scores(model, baseline, ds)
    return TrainResult(model=model, baseline=baseline, holdout=holdout_df.reset_index(drop=True), metrics=metrics)
