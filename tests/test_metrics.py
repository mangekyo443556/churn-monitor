import numpy as np
import pandas as pd
import pytest

from process_drift.metrics import CATEGORICAL_METRICS, NUMERIC_METRICS


@pytest.fixture
def normal_sample() -> "pd.Series[float]":
    return pd.Series(np.random.default_rng(1).normal(50, 10, size=3000))


@pytest.mark.parametrize("name", sorted(NUMERIC_METRICS))
def test_identical_distributions_give_almost_zero(name: str, normal_sample: "pd.Series[float]") -> None:
    other = pd.Series(np.random.default_rng(2).normal(50, 10, size=3000))
    assert NUMERIC_METRICS[name](normal_sample, other) < 0.1


@pytest.mark.parametrize("name", sorted(NUMERIC_METRICS))
def test_shifted_distribution_gives_more_drift(name: str, normal_sample: "pd.Series[float]") -> None:
    same = pd.Series(np.random.default_rng(2).normal(50, 10, size=3000))
    shifted = pd.Series(np.random.default_rng(3).normal(65, 10, size=3000))
    metric = NUMERIC_METRICS[name]
    assert metric(normal_sample, shifted) > metric(normal_sample, same) * 3


def test_psi_known_value_for_two_bins() -> None:
    """PSI con proporciones conocidas, calculado a mano:
    referencia 50/50, actual 80/20 -> (0.8-0.5)ln(0.8/0.5) + (0.2-0.5)ln(0.2/0.5) = 0.4159
    """
    ref = pd.Series(["A"] * 50 + ["B"] * 50)
    cur = pd.Series(["A"] * 80 + ["B"] * 20)
    assert CATEGORICAL_METRICS["psi"](ref, cur) == pytest.approx(0.4159, abs=1e-3)


def test_new_category_in_production_is_detected() -> None:
    ref = pd.Series(["A"] * 100)
    cur = pd.Series(["A"] * 50 + ["Z"] * 50)
    assert CATEGORICAL_METRICS["jensenshannon"](ref, cur) > 0.3


def test_constant_reference_column_does_not_crash() -> None:
    assert NUMERIC_METRICS["psi"](pd.Series([1.0] * 50), pd.Series([1.0] * 50)) == pytest.approx(0.0, abs=1e-3)
