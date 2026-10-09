"""Convierte el reporte de drift en un mensaje legible para Slack."""
from typing import Any, Dict, List


def _format_drift(drift: Dict[str, Any]) -> List[str]:
    icon = ":rotating_light:" if drift["alert"] else ":white_check_mark:"
    lines = [f"{icon} *{drift['name']}* ({drift['type']}) · {drift['share_drifted']:.0%} de features con drift"]
    top = sorted(drift["features"], key=lambda f: f["score"], reverse=True)[:5]
    for f in top:
        mark = "⚠️" if f["drifted"] else "·"
        lines.append(f"    {mark} `{f['feature']}` {f['algorithm']}={f['score']:.3f} (umbral {f['threshold']})")
    return lines


def build_message(report: Dict[str, Any]) -> str:
    header = ":rotating_light: Drift detectado" if report["alert"] else ":white_check_mark: Sin drift relevante"
    summary = report.get("score_summary", {})
    lines = [
        f"{header} · *{report['model_name']}* · {report['date']}",
        f"Escenario simulado: `{report['scenario']}` · {report['rows']} filas",
        f"Score promedio: entrenamiento {summary.get('baseline_mean_score', 0):.3f} "
        f"→ hoy {summary.get('current_mean_score', 0):.3f}",
        "",
    ]
    for drift in report["drifts"]:
        lines.extend(_format_drift(drift))
    return "\n".join(lines)
