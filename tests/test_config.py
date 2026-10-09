from typing import Any, Dict

import pytest

from commons.config import AppConfig, ConfigError, parse_config


def _minimal() -> Dict[str, Any]:
    return {
        "model_name": "m",
        "dataset": {"raw_key": "k", "id_column": "id", "target": "y", "positive_label": "1",
                    "numeric_features": ["a"], "categorical_features": ["b"]},
        "drifts": [{"name": "d", "type": "input", "numeric_algorithm": "psi", "threshold": 0.2}],
        "simulation": {"default_scenario": "none", "scenarios": {"none": []}},
    }


def test_real_config_file_is_valid(config: AppConfig) -> None:
    assert config.model_name == "churn-v1"
    assert len(config.enabled_drifts) >= 1
    assert config.simulation.default_scenario in config.simulation.scenarios


def test_minimal_config_parses() -> None:
    cfg = parse_config(_minimal())
    assert cfg.dataset.features == ["a", "b"]


@pytest.mark.parametrize(
    "path, value",
    [
        (("drifts", 0, "numeric_algorithm"), "magia"),
        (("drifts", 0, "type"), "otro"),
        (("simulation", "default_scenario"), "no_existe"),
    ],
)
def test_invalid_values_raise_clear_error(path: tuple, value: str) -> None:  # type: ignore[type-arg]
    raw = _minimal()
    target: Any = raw
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ConfigError):
        parse_config(raw)


def test_missing_key_names_the_key() -> None:
    raw = _minimal()
    del raw["dataset"]["target"]
    with pytest.raises(ConfigError, match="target"):
        parse_config(raw)
