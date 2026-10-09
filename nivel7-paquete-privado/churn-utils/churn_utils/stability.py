"""Population Stability Index, empaquetado para reutilizarlo en varios proyectos."""
from typing import Sequence

import numpy as np


def psi(reference: Sequence[float], current: Sequence[float], bins: int = 10) -> float:
    """PSI entre dos muestras numéricas. 0 = iguales; más alto = más drift."""
    ref = np.asarray(reference, dtype=float)
    cur = np.asarray(current, dtype=float)
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1))).astype(float)
    if len(edges) < 2:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    p = np.clip(np.histogram(ref, edges)[0] / len(ref), 1e-6, None)
    q = np.clip(np.histogram(cur, edges)[0] / len(cur), 1e-6, None)
    return float(np.sum((q - p) * np.log(q / p)))


def psi_label(value: float) -> str:
    """Traduce un PSI a palabras, con los cortes que se usan en riesgo crediticio."""
    if value < 0.1:
        return "estable"
    if value < 0.25:
        return "cambio moderado"
    return "cambio fuerte"
