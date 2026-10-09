import pandas as pd

from commons.config import AppConfig, ScenarioStep
from simulate_production.domain import simulate_batch
from train_model.domain import SCORE_COLUMN, clean_dataset, train


def test_clean_dataset_fixes_types_and_target(telco_like: pd.DataFrame, config: AppConfig) -> None:
    df = clean_dataset(telco_like, config.dataset)
    assert len(df) == len(telco_like) - 1          # se quitó la fila con TotalCharges vacío
    assert df["TotalCharges"].dtype.kind == "f"
    assert set(df["Churn"].unique()) <= {0, 1}
    assert df["SeniorCitizen"].dtype == object      # categórica como texto


def test_train_learns_something(telco_like: pd.DataFrame, config: AppConfig) -> None:
    result = train(telco_like, config.dataset)
    assert result.metrics["auc_holdout"] > 0.6
    assert SCORE_COLUMN in result.baseline.columns
    assert result.metrics["rows_train"] + result.metrics["rows_holdout"] == len(telco_like) - 1


def test_no_scenario_samples_requested_size(telco_like: pd.DataFrame) -> None:
    batch = simulate_batch(telco_like, [], size=250, seed=1)
    assert len(batch) == 250


def test_scale_multiplies_column(telco_like: pd.DataFrame) -> None:
    step = ScenarioStep(op="scale", column="MonthlyCharges", factor=2.0)
    base = simulate_batch(telco_like, [], size=300, seed=1)
    scaled = simulate_batch(telco_like, [step], size=300, seed=1)
    assert scaled["MonthlyCharges"].mean() == base["MonthlyCharges"].mean() * 2.0


def test_oversample_reaches_requested_share(telco_like: pd.DataFrame) -> None:
    step = ScenarioStep(op="oversample", column="tenure", condition="lt", value=12, share=0.8)
    batch = simulate_batch(telco_like, [step], size=500, seed=1)
    assert (batch["tenure"] < 12).mean() == 0.8


def test_same_seed_same_batch(telco_like: pd.DataFrame) -> None:
    a = simulate_batch(telco_like, [], size=100, seed=7)
    b = simulate_batch(telco_like, [], size=100, seed=7)
    pd.testing.assert_frame_equal(a, b)
