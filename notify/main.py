"""Lambda 4 (paso 3 de la Step Function): publica el resumen en Slack.

Entrada (event):  {"report_key": "..."}  (la salida de process_drift)
                  o {"report": {...}}     (el reporte completo, útil para probar sin datos)
Salida:           {"sent": bool, "text": "..."}

Si SLACK_WEBHOOK_URL está vacía, NO envía nada: solo imprime el mensaje.
Así puedes probar todo sin Slack (modo "dry run").
Con NOTIFY_ONLY_ON_ALERT=true, solo envía cuando hay alerta.
"""
import json
import os
import urllib.request
from typing import Any, Dict

from commons.logger import logger
from commons.storage import get_storage, read_json
from notify.domain import build_message


def send_to_slack(webhook_url: str, text: str) -> None:
    """Un webhook de Slack es una URL secreta: le haces POST con {"text": ...} y aparece en el canal."""
    request = urllib.request.Request(
        webhook_url,
        data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 - URL configurada por el dueño
        if response.status != 200:
            raise RuntimeError(f"Slack respondió {response.status}")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    event = event or {}
    if "report" in event:
        report: Dict[str, Any] = event["report"]
    elif "report_key" in event:
        report = read_json(get_storage(), event["report_key"])
    else:
        raise ValueError("El evento necesita 'report_key' o 'report'")

    text = build_message(report)
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    only_on_alert = os.environ.get("NOTIFY_ONLY_ON_ALERT", "false").lower() == "true"

    if only_on_alert and not report["alert"]:
        logger.info("Sin alerta y NOTIFY_ONLY_ON_ALERT=true: no se envía nada")
        return {"sent": False, "text": text}
    if not webhook:
        logger.info("SLACK_WEBHOOK_URL vacía (dry run). Mensaje que se habría enviado:\n" + text)
        return {"sent": False, "text": text}

    send_to_slack(webhook, text)
    logger.info("Mensaje enviado a Slack")
    return {"sent": True, "text": text}
