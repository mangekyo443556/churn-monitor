"""Test de punta a punta: corre las 4 Lambdas en orden sobre una carpeta temporal."""
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest

from commons.storage import get_storage, write_csv
from notify.main import handler as notify_handler
from process_drift.main import handler as drift_handler
from simulate_production.main import handler as simulate_handler
from train_model.main import handler as train_handler


@pytest.fixture
def trained(local_bucket: Path, telco_like: pd.DataFrame) -> Path:
    write_csv(get_storage(), "data/raw/telco.csv", telco_like)
    train_handler({}, None)
    return local_bucket


def _monitor(scenario: str) -> Dict[str, Any]:
    out = simulate_handler({"scenario": scenario, "date": "2026-01-01", "seed": 3}, None)
    return drift_handler(out, None)


def test_train_writes_all_artifacts(trained: Path) -> None:
    prefix = trained / "models" / "churn-v1"
    for name in ["model.joblib", "baseline.csv", "holdout.csv", "metadata.json"]:
        assert (prefix / name).exists(), name


def test_no_drift_scenario_does_not_alert(trained: Path) -> None:
    result = _monitor("none")
    assert result["alert"] is False
    assert (trained / result["report_key"]).exists()


def test_price_increase_is_detected_in_monthly_charges(trained: Path) -> None:
    result = _monitor("price_increase")
    assert result["alert"] is True
    assert "MonthlyCharges" in result["drifted"]


def test_notify_runs_in_dry_run_mode(trained: Path) -> None:
    result = notify_handler(_monitor("contract_shift"), None)
    assert result["sent"] is False
    assert "churn-v1" in result["text"]


def test_unknown_scenario_fails_clearly(trained: Path) -> None:
    with pytest.raises(ValueError, match="no existe"):
        simulate_handler({"scenario": "inventado"}, None)
