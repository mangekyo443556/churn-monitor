"""Métricas de drift, implementadas a mano para que se entienda qué calculan.

Todas comparan dos muestras de una misma columna:
    reference = cómo se veía en entrenamiento (baseline)
    current   = cómo se ve hoy en producción (batch)
y devuelven un número >= 0: 0 = iguales, más alto = más diferentes.

pipeline-model-monitor usa la librería Evidently, que calcula estas mismas
métricas (y más). Ver docs/nivel-2.md para el ejercicio de cambiar a Evidently.
"""
from typing import Any, Callable, Dict, Tuple

import numpy as np
import numpy.typing as npt
import pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import ks_2samp, wasserstein_distance

EPS = 1e-6  # evita log(0) y divisiones por cero

FloatArray = npt.NDArray[np.float64]


def _clean(values: "pd.Series[Any]") -> FloatArray:
    arr: FloatArray = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    return arr


def _numeric_histograms(ref: FloatArray, cur: FloatArray, bins: int = 10) -> Tuple[FloatArray, FloatArray]:
    """Reparte ambas muestras en los mismos 'cajones' (deciles de la referencia).

    Devuelve la proporción de filas en cada cajón para cada muestra.
    """
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 2:  # columna constante en la referencia
        edges = np.array([ref.min() - 0.5, ref.min() + 0.5])
    edges = edges.astype(float)
    edges[0], edges[-1] = -np.inf, np.inf  # lo que caiga fuera del rango original también cuenta
    ref_counts = np.histogram(ref, bins=edges)[0].astype(float)
    cur_counts = np.histogram(cur, bins=edges)[0].astype(float)
    return ref_counts / ref_counts.sum(), cur_counts / cur_counts.sum()


def _category_distributions(ref: "pd.Series[Any]", cur: "pd.Series[Any]") -> Tuple[FloatArray, FloatArray]:
    """Proporción de cada categoría en ambas muestras, alineadas por categoría."""
    ref_freq = ref.astype(str).value_counts(normalize=True)
    cur_freq = cur.astype(str).value_counts(normalize=True)
    categories = sorted(set(ref_freq.index) | set(cur_freq.index))
    p = ref_freq.reindex(categories, fill_value=0.0).to_numpy(dtype=float)
    q = cur_freq.reindex(categories, fill_value=0.0).to_numpy(dtype=float)
    return p, q


def _psi_from_distributions(p: FloatArray, q: FloatArray) -> float:
    """Population Stability Index: suma de (actual - esperado) * ln(actual / esperado)."""
    p = np.clip(p, EPS, None)
    q = np.clip(q, EPS, None)
    return float(np.sum((q - p) * np.log(q / p)))


def _js_from_distributions(p: FloatArray, q: FloatArray) -> float:
    """Distancia de Jensen-Shannon en base 2: siempre entre 0 y 1."""
    return float(jensenshannon(p, q, base=2))


# --- Métricas numéricas -------------------------------------------------------

def psi_numeric(ref: "pd.Series[Any]", cur: "pd.Series[Any]") -> float:
    return _psi_from_distributions(*_numeric_histograms(_clean(ref), _clean(cur)))


def js_numeric(ref: "pd.Series[Any]", cur: "pd.Series[Any]") -> float:
    return _js_from_distributions(*_numeric_histograms(_clean(ref), _clean(cur)))


def ks_numeric(ref: "pd.Series[Any]", cur: "pd.Series[Any]") -> float:
    """Kolmogorov-Smirnov: máxima distancia entre las dos curvas acumuladas (0 a 1)."""
    return float(ks_2samp(_clean(ref), _clean(cur)).statistic)


def wasserstein_numeric(ref: "pd.Series[Any]", cur: "pd.Series[Any]") -> float:
    """Wasserstein ("cuánta tierra hay que mover"), dividido por la desviación de la referencia
    para que no dependa de las unidades de la columna."""
    r, c = _clean(ref), _clean(cur)
    scale = float(np.std(r)) or 1.0
    return float(wasserstein_distance(r, c) / scale)


# --- Métricas categóricas -----------------------------------------------------

def psi_categorical(ref: "pd.Series[Any]", cur: "pd.Series[Any]") -> float:
    return _psi_from_distributions(*_category_distributions(ref, cur))


def js_categorical(ref: "pd.Series[Any]", cur: "pd.Series[Any]") -> float:
    return _js_from_distributions(*_category_distributions(ref, cur))


Metric = Callable[["pd.Series[Any]", "pd.Series[Any]"], float]

NUMERIC_METRICS: Dict[str, Metric] = {
    "psi": psi_numeric,
    "ks": ks_numeric,
    "wasserstein": wasserstein_numeric,
    "jensenshannon": js_numeric,
}

CATEGORICAL_METRICS: Dict[str, Metric] = {
    "psi": psi_categorical,
    "jensenshannon": js_categorical,
}
