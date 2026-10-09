"""Corre las Lambdas en tu máquina, en el mismo orden que la Step Function.

Cada paso llama al `handler` de su Lambda con un evento, igual que AWS.
La salida de un paso es el evento del siguiente.

Uso:
    poetry run python local_runs/run_pipeline.py train
    poetry run python local_runs/run_pipeline.py monitor --scenario price_increase
    poetry run python local_runs/run_pipeline.py all --scenario new_customers

Equivale a la carpeta local_runs/ de pipeline-model-monitor.
"""
import argparse
import json
import os
import pathlib
import sys
from typing import Any, Dict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.environ.setdefault("STORAGE", "local")

from notify.main import handler as notify_handler  # noqa: E402
from process_drift.main import handler as drift_handler  # noqa: E402
from simulate_production.main import handler as simulate_handler  # noqa: E402
from train_model.main import handler as train_handler  # noqa: E402


def show(title: str, payload: Dict[str, Any]) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def run_monitor(scenario: str | None, date: str | None) -> None:
    event: Dict[str, Any] = {}
    if scenario:
        event["scenario"] = scenario
    if date:
        event["date"] = date
    out1 = simulate_handler(event, None)
    show("1. simulate_production", out1)
    out2 = drift_handler(out1, None)
    show("2. process_drift", out2)
    out3 = notify_handler(out2, None)
    print("\n=== 3. notify ===")
    print(out3["text"])
    print(f"\n(enviado a Slack: {out3['sent']})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", choices=["train", "monitor", "all"])
    parser.add_argument("--scenario", default=None, help="none | price_increase | new_customers | contract_shift")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD (por defecto, hoy)")
    args = parser.parse_args()

    if args.step in ("train", "all"):
        show("0. train_model", train_handler({}, None))
    if args.step in ("monitor", "all"):
        run_monitor(args.scenario, args.date)


if __name__ == "__main__":
    main()
