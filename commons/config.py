"""Lee config/drifts.yaml y lo convierte en objetos de Python con tipos.

Validar la configuración al cargarla hace que un error de tipeo en el YAML
falle de inmediato con un mensaje claro, en lugar de romper a mitad del análisis.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "drifts.yaml"

NUMERIC_ALGORITHMS = {"psi", "ks", "wasserstein", "jensenshannon"}
CATEGORICAL_ALGORITHMS = {"psi", "jensenshannon"}
SCENARIO_OPS = {"scale", "oversample"}
CONDITIONS = {"lt", "gt", "eq"}


class ConfigError(ValueError):
    """La configuración tiene un valor inválido."""


@dataclass(frozen=True)
class DatasetConfig:
    raw_key: str
    id_column: str
    target: str
    positive_label: str
    numeric_features: List[str]
    categorical_features: List[str]

    @property
    def features(self) -> List[str]:
        return self.numeric_features + self.categorical_features


@dataclass(frozen=True)
class DriftConfig:
    name: str
    type: str
    numeric_algorithm: str
    threshold: float
    categorical_algorithm: str = "jensenshannon"
    alert_share: float = 0.0
    enabled: bool = True


@dataclass(frozen=True)
class ScenarioStep:
    op: str
    column: str
    factor: float = 1.0
    condition: str = "eq"
    value: Any = None
    share: float = 0.5


@dataclass(frozen=True)
class SimulationConfig:
    batch_size: int
    default_scenario: str
    scenarios: Dict[str, List[ScenarioStep]] = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfig:
    model_name: str
    dataset: DatasetConfig
    drifts: List[DriftConfig]
    simulation: SimulationConfig

    @property
    def enabled_drifts(self) -> List[DriftConfig]:
        return [d for d in self.drifts if d.enabled]


def _require(data: Dict[str, Any], key: str, where: str) -> Any:
    if key not in data:
        raise ConfigError(f"Falta la clave '{key}' en {where}")
    return data[key]


def _parse_drift(raw: Dict[str, Any]) -> DriftConfig:
    drift = DriftConfig(
        name=str(_require(raw, "name", "drifts")),
        type=str(_require(raw, "type", "drifts")),
        numeric_algorithm=str(_require(raw, "numeric_algorithm", "drifts")),
        threshold=float(_require(raw, "threshold", "drifts")),
        categorical_algorithm=str(raw.get("categorical_algorithm", "jensenshannon")),
        alert_share=float(raw.get("alert_share", 0.0)),
        enabled=bool(raw.get("enabled", True)),
    )
    if drift.type not in {"input", "output"}:
        raise ConfigError(f"drift '{drift.name}': type debe ser input u output")
    if drift.numeric_algorithm not in NUMERIC_ALGORITHMS:
        raise ConfigError(f"drift '{drift.name}': numeric_algorithm '{drift.numeric_algorithm}' no existe")
    if drift.categorical_algorithm not in CATEGORICAL_ALGORITHMS:
        raise ConfigError(
            f"drift '{drift.name}': categorical_algorithm '{drift.categorical_algorithm}' no existe"
        )
    return drift


def _parse_step(raw: Dict[str, Any], scenario: str) -> ScenarioStep:
    step = ScenarioStep(
        op=str(_require(raw, "op", f"escenario {scenario}")),
        column=str(_require(raw, "column", f"escenario {scenario}")),
        factor=float(raw.get("factor", 1.0)),
        condition=str(raw.get("condition", "eq")),
        value=raw.get("value"),
        share=float(raw.get("share", 0.5)),
    )
    if step.op not in SCENARIO_OPS:
        raise ConfigError(f"escenario {scenario}: op '{step.op}' no existe ({sorted(SCENARIO_OPS)})")
    if step.op == "oversample":
        if step.condition not in CONDITIONS:
            raise ConfigError(f"escenario {scenario}: condition '{step.condition}' no existe")
        if not 0.0 < step.share <= 1.0:
            raise ConfigError(f"escenario {scenario}: share debe estar entre 0 y 1")
    return step


def parse_config(raw: Dict[str, Any]) -> AppConfig:
    ds_raw = _require(raw, "dataset", "la raíz")
    dataset = DatasetConfig(
        raw_key=str(_require(ds_raw, "raw_key", "dataset")),
        id_column=str(_require(ds_raw, "id_column", "dataset")),
        target=str(_require(ds_raw, "target", "dataset")),
        positive_label=str(_require(ds_raw, "positive_label", "dataset")),
        numeric_features=[str(c) for c in ds_raw.get("numeric_features", [])],
        categorical_features=[str(c) for c in ds_raw.get("categorical_features", [])],
    )
    if not dataset.features:
        raise ConfigError("dataset: define al menos una feature")

    sim_raw = _require(raw, "simulation", "la raíz")
    scenarios = {
        str(name): [_parse_step(s, str(name)) for s in (steps or [])]
        for name, steps in (sim_raw.get("scenarios") or {}).items()
    }
    simulation = SimulationConfig(
        batch_size=int(sim_raw.get("batch_size", 1000)),
        default_scenario=str(sim_raw.get("default_scenario", "none")),
        scenarios=scenarios,
    )
    if simulation.default_scenario not in scenarios:
        raise ConfigError(f"default_scenario '{simulation.default_scenario}' no está en scenarios")

    return AppConfig(
        model_name=str(_require(raw, "model_name", "la raíz")),
        dataset=dataset,
        drifts=[_parse_drift(d) for d in _require(raw, "drifts", "la raíz")],
        simulation=simulation,
    )


def load_config(path: Optional[Path] = None) -> AppConfig:
    """Carga la configuración.

    Orden de prioridad: argumento `path` > variable DRIFTS_CONFIG_PATH > config/drifts.yaml.
    """
    config_path = path or Path(os.environ.get("DRIFTS_CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))
    with open(config_path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    if not isinstance(raw, dict):
        raise ConfigError(f"{config_path} no contiene un diccionario YAML")
    return parse_config(raw)
