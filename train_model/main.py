"""Lambda 1: entrena el modelo y guarda la referencia (baseline).

Se corre una vez (o cuando quieras reentrenar), no todos los días.

Entrada (event):  {"seed": 42}   (opcional)
Salida:           metadatos del modelo entrenado
"""
import io
from datetime import datetime, timezone
from typing import Any, Dict

import joblib
from sklearn.pipeline import Pipeline

from commons.config import load_config
from commons.logger import logger
from commons.storage import Storage, get_storage, model_prefix, read_csv, write_csv, write_json
from train_model.domain import train


def save_model(storage: Storage, key: str, model: Pipeline) -> None:
    buffer = io.BytesIO()
    joblib.dump(model, buffer)
    storage.write_bytes(key, buffer.getvalue())


def load_model(storage: Storage, key: str) -> Pipeline:
    model: Pipeline = joblib.load(io.BytesIO(storage.read_bytes(key)))
    return model


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    config = load_config()
    storage = get_storage()
    seed = int((event or {}).get("seed", 42))

    logger.info(f"Leyendo dataset desde {storage.describe(config.dataset.raw_key)}")
    raw = read_csv(storage, config.dataset.raw_key)

    result = train(raw, config.dataset, seed=seed)
    prefix = model_prefix(config.model_name)

    save_model(storage, f"{prefix}/model.joblib", result.model)
    write_csv(storage, f"{prefix}/baseline.csv", result.baseline)
    write_csv(storage, f"{prefix}/holdout.csv", result.holdout)

    metadata = {
        "model_name": config.model_name,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": seed,
        "features": config.dataset.features,
        "metrics": result.metrics,
        "artifacts_prefix": storage.describe(prefix),
    }
    write_json(storage, f"{prefix}/metadata.json", metadata)
    logger.info(f"Modelo entrenado: {result.metrics}")
    return metadata
