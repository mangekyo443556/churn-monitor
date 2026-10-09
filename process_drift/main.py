"""Lambda 3 (paso 2 de la Step Function): calcula el drift del batch del día.

Entrada (event):  la salida de simulate_production -> {"date", "scenario", "batch_key", ...}
Salida:           {"date", "report_key", "alert", "drifted"}  -> va a notify
"""
from typing import Any, Dict, List

import pandas as pd

from commons.config import load_config
from commons.logger import logger
from commons.storage import get_storage, model_prefix, read_csv, report_key, write_json
from process_drift.domain import DriftResult, build_report, compute_input_drift, compute_output_drift
from train_model.domain import SCORE_COLUMN, clean_dataset, predict_scores
from train_model.main import load_model


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    event = event or {}
    if "batch_key" not in event or "date" not in event:
        raise ValueError("El evento necesita 'batch_key' y 'date' (la salida de simulate_production)")

    config = load_config()
    storage = get_storage()
    ds = config.dataset
    prefix = model_prefix(config.model_name)

    baseline = read_csv(storage, f"{prefix}/baseline.csv")
    model = load_model(storage, f"{prefix}/model.joblib")
    batch = clean_dataset(read_csv(storage, event["batch_key"]), ds)
    current_scores = pd.Series(predict_scores(model, batch, ds))

    results: List[DriftResult] = []
    for drift in config.enabled_drifts:
        if drift.type == "input":
            results.append(compute_input_drift(baseline, batch, ds, drift))
        else:
            results.append(compute_output_drift(baseline[SCORE_COLUMN], current_scores, drift))
        logger.info(f"{drift.name}: alert={results[-1].alert} drifted={results[-1].drifted_features}")

    score_summary = {
        "baseline_mean_score": round(float(baseline[SCORE_COLUMN].mean()), 4),
        "current_mean_score": round(float(current_scores.mean()), 4),
    }
    report = build_report(
        config.model_name, event["date"], str(event.get("scenario", "desconocido")),
        int(len(batch)), results, score_summary,
    )
    key = report_key(config.model_name, event["date"])
    write_json(storage, key, report)
    logger.info(f"Reporte guardado en {storage.describe(key)} · alert={report['alert']}")

    drifted = sorted({f for r in results for f in r.drifted_features})
    return {"date": event["date"], "report_key": key, "alert": report["alert"], "drifted": drifted}
