"""Fabrica un batch de "producción" a partir del holdout, aplicando un escenario.

En un sistema real los datos de producción llegan solos (en Vana, las
evaluaciones que se guardan en S3 cada día). Aquí los simulamos para poder
provocar drift a voluntad y ver si el monitor lo detecta.
"""
from typing import List

import numpy as np
import pandas as pd

from commons.config import ScenarioStep


def _condition_mask(df: pd.DataFrame, step: ScenarioStep) -> "pd.Series[bool]":
    col = df[step.column]
    mask: "pd.Series[bool]"
    if step.condition == "lt":
        mask = col < step.value
    elif step.condition == "gt":
        mask = col > step.value
    else:
        mask = col.astype(str) == str(step.value)
    return mask


def _sample(df: pd.DataFrame, n: int, rng: np.random.Generator) -> pd.DataFrame:
    if n <= 0 or df.empty:
        return df.iloc[0:0]
    replace = n > len(df)
    idx = rng.choice(len(df), size=n, replace=replace)
    return df.iloc[idx]


def oversample(pool: pd.DataFrame, step: ScenarioStep, size: int, rng: np.random.Generator) -> pd.DataFrame:
    """Arma un batch donde `share` de las filas cumplen la condición."""
    mask = _condition_mask(pool, step)
    matching, others = pool[mask], pool[~mask]
    if matching.empty:
        raise ValueError(f"Ninguna fila cumple {step.column} {step.condition} {step.value}")
    n_match = int(round(size * step.share))
    batch = pd.concat([_sample(matching, n_match, rng), _sample(others, size - n_match, rng)])
    return batch.sample(frac=1.0, random_state=int(rng.integers(0, 2**31 - 1))).reset_index(drop=True)


def simulate_batch(
    holdout: pd.DataFrame, steps: List[ScenarioStep], size: int, seed: int = 0
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    batch = _sample(holdout, size, rng).reset_index(drop=True)
    for step in steps:
        if step.op == "oversample":
            batch = oversample(holdout, step, size, rng)
        elif step.op == "scale":
            batch[step.column] = batch[step.column] * step.factor
    return batch.reset_index(drop=True)
