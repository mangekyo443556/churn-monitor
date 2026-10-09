"""Dónde se guardan los archivos: una carpeta local o un bucket de S3.

El resto del código solo habla de "llaves" (por ejemplo
`models/churn-v1/model.joblib`) y no sabe si está en tu disco o en AWS.
Así el mismo código corre en tu máquina (Nivel 2), en Docker (Nivel 4)
y en Lambda (Nivel 6). Solo cambia la variable de entorno STORAGE.

    STORAGE=local  -> archivos en LOCAL_DATA_DIR (por defecto ./.local_bucket)
    STORAGE=s3     -> archivos en el bucket DATA_BUCKET

Es la misma idea que los "adapters" de pipeline-model-monitor.
"""
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, Protocol

import pandas as pd

from commons.config import PROJECT_ROOT


class Storage(Protocol):
    """Lo mínimo que necesitamos de un almacenamiento."""

    def read_bytes(self, key: str) -> bytes: ...

    def write_bytes(self, key: str, data: bytes) -> None: ...

    def exists(self, key: str) -> bool: ...

    def describe(self, key: str) -> str: ...


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, key: str) -> Path:
        return self.root / key

    def read_bytes(self, key: str) -> bytes:
        path = self._path(key)
        if not path.exists():
            raise FileNotFoundError(f"No existe {path}. ¿Corriste los pasos anteriores?")
        return path.read_bytes()

    def write_bytes(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def describe(self, key: str) -> str:
        return str(self._path(key))


class S3Storage:
    def __init__(self, bucket: str, client: Any = None) -> None:
        import boto3  # se importa aquí para que el modo local no dependa de AWS

        self.bucket = bucket
        self.client = client or boto3.client("s3")

    def read_bytes(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        body: bytes = response["Body"].read()
        return body

    def write_bytes(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:  # noqa: BLE001 - head_object lanza ClientError si no existe
            return False

    def describe(self, key: str) -> str:
        return f"s3://{self.bucket}/{key}"


def get_storage() -> Storage:
    """Elige el almacenamiento según las variables de entorno."""
    kind = os.environ.get("STORAGE", "local").lower()
    if kind == "s3":
        bucket = os.environ.get("DATA_BUCKET")
        if not bucket:
            raise RuntimeError("STORAGE=s3 requiere la variable DATA_BUCKET")
        return S3Storage(bucket)
    if kind == "local":
        root = Path(os.environ.get("LOCAL_DATA_DIR", str(PROJECT_ROOT / ".local_bucket")))
        return LocalStorage(root)
    raise RuntimeError(f"STORAGE debe ser 'local' o 's3', no '{kind}'")


# --- Ayudas para leer/escribir formatos comunes -------------------------------

def read_csv(storage: Storage, key: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(storage.read_bytes(key)))


def write_csv(storage: Storage, key: str, df: pd.DataFrame) -> None:
    storage.write_bytes(key, df.to_csv(index=False).encode("utf-8"))


def read_json(storage: Storage, key: str) -> Dict[str, Any]:
    data: Dict[str, Any] = json.loads(storage.read_bytes(key).decode("utf-8"))
    return data


def write_json(storage: Storage, key: str, data: Dict[str, Any]) -> None:
    storage.write_bytes(key, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))


# --- Convención de llaves (la "estructura de carpetas" del bucket) ------------

def model_prefix(model_name: str) -> str:
    return f"models/{model_name}"


def batch_key(model_name: str, date: str) -> str:
    return f"production/{model_name}/date={date}/batch.csv"


def report_key(model_name: str, date: str) -> str:
    return f"reports/{model_name}/date={date}/drift_report.json"
