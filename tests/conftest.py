"""Datos de prueba compartidos por todos los tests.

Los tests NO usan el CSV real: generan un dataset sintético pequeño con las
mismas columnas. Así corren rápido, sin internet, y en GitHub Actions.
"""
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd
import pytest

from commons.config import AppConfig, load_config


@pytest.fixture
def config() -> AppConfig:
    return load_config()


@pytest.fixture
def telco_like() -> pd.DataFrame:
    """600 clientes falsos con la estructura del dataset Telco."""
    rng = np.random.default_rng(0)
    n = 600
    tenure = rng.integers(0, 72, size=n)
    monthly = rng.uniform(20, 110, size=n).round(2)
    contract = rng.choice(["Month-to-month", "One year", "Two year"], size=n, p=[0.55, 0.25, 0.2])
    # Más churn si el contrato es mes a mes y la antigüedad es baja: así el modelo aprende algo.
    p_churn = 0.1 + 0.35 * (contract == "Month-to-month") + 0.2 * (tenure < 12)
    yes_no = ["Yes", "No"]
    df = pd.DataFrame({
        "customerID": [f"C{i:04d}" for i in range(n)],
        "gender": rng.choice(["Male", "Female"], size=n),
        "SeniorCitizen": rng.choice([0, 1], size=n, p=[0.84, 0.16]),
        "Partner": rng.choice(yes_no, size=n),
        "Dependents": rng.choice(yes_no, size=n),
        "tenure": tenure,
        "PhoneService": rng.choice(yes_no, size=n, p=[0.9, 0.1]),
        "InternetService": rng.choice(["DSL", "Fiber optic", "No"], size=n),
        "OnlineSecurity": rng.choice(["Yes", "No", "No internet service"], size=n),
        "TechSupport": rng.choice(["Yes", "No", "No internet service"], size=n),
        "Contract": contract,
        "PaperlessBilling": rng.choice(yes_no, size=n),
        "PaymentMethod": rng.choice(["Electronic check", "Mailed check", "Bank transfer (automatic)"], size=n),
        "MonthlyCharges": monthly,
        "TotalCharges": (monthly * np.maximum(tenure, 1)).round(2).astype(str),
        "Churn": np.where(rng.uniform(size=n) < p_churn, "Yes", "No"),
    })
    df.loc[0, "TotalCharges"] = " "  # igual que el dataset real: un valor vacío
    return df


@pytest.fixture
def local_bucket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Una carpeta temporal que hace de bucket; se borra al terminar el test."""
    monkeypatch.setenv("STORAGE", "local")
    monkeypatch.setenv("LOCAL_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    yield tmp_path
