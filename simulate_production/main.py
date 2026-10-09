"""Lambda 2 (paso 1 de la Step Function): genera el batch de producción del día.

Entrada (event):  {"scenario": "price_increase", "date": "2026-10-08", "seed": 7}
                  Todo es opcional: sin scenario usa default_scenario,
                  sin date usa la fecha de hoy (UTC).
Salida:           {"date", "scenario", "batch_key", "rows"}  -> va al siguiente paso
"""
import zlib
from datetime import datetime, timezone
from typing import Any, Dict

from commons.config import load_config
from commons.logger import logger
from commons.storage import batch_key, get_storage, model_prefix, read_csv, write_csv
from simulate_production.domain import simulate_batch


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    event = event or {}
    config = load_config()
    storage = get_storage()

    scenario = str(event.get("scenario") or config.simulation.default_scenario)
    if scenario not in config.simulation.scenarios:
        raise ValueError(f"Escenario '{scenario}' no existe. Opciones: {sorted(config.simulation.scenarios)}")
    date = str(event.get("date") or datetime.now(timezone.utc).date().isoformat())
    # Semilla estable por fecha: el mismo día genera siempre el mismo batch.
    seed = int(event.get("seed", zlib.crc32(date.encode())))

    holdout = read_csv(storage, f"{model_prefix(config.model_name)}/holdout.csv")
    batch = simulate_batch(holdout, config.simulation.scenarios[scenario], config.simulation.batch_size, seed)

    key = batch_key(config.model_name, date)
    write_csv(storage, key, batch)
    logger.info(f"Batch '{scenario}' de {len(batch)} filas guardado en {storage.describe(key)}")
    return {"date": date, "scenario": scenario, "batch_key": key, "rows": int(len(batch))}
