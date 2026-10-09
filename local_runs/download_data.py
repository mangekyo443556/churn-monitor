"""Descarga el dataset Telco Customer Churn a la carpeta local que hace de "bucket".

Uso:  poetry run python local_runs/download_data.py
      (o simplemente: make data)

El mismo CSV está en Kaggle ("Telco Customer Churn", de blastchar). Aquí se baja
de la copia pública que IBM publica en GitHub, para no necesitar cuenta de Kaggle.
Si prefieres Kaggle, descárgalo a mano y cópialo a .local_bucket/data/raw/telco.csv
"""
import pathlib
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from commons.config import load_config  # noqa: E402
from commons.storage import get_storage  # noqa: E402

URL = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"


def main() -> None:
    config = load_config()
    storage = get_storage()
    key = config.dataset.raw_key
    if storage.exists(key):
        print(f"Ya existe {storage.describe(key)}; no se descarga de nuevo.")
        return
    print(f"Descargando {URL} ...")
    with urllib.request.urlopen(URL, timeout=60) as response:  # noqa: S310
        data = response.read()
    storage.write_bytes(key, data)
    print(f"Listo: {len(data) / 1024:.0f} KB en {storage.describe(key)}")


if __name__ == "__main__":
    main()
