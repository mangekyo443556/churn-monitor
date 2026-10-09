from typing import Any, Dict, List

import boto3
import pytest
from moto import mock_aws

from commons.storage import S3Storage, get_storage, read_json, write_json
from notify import main as notify_main
from notify.domain import build_message


def _report(alert: bool) -> Dict[str, Any]:
    return {
        "model_name": "churn-v1", "date": "2026-01-01", "scenario": "x", "rows": 10, "alert": alert,
        "score_summary": {"baseline_mean_score": 0.25, "current_mean_score": 0.4},
        "drifts": [{
            "name": "feature_drift", "type": "input", "alert": alert, "share_drifted": 0.5,
            "drifted_features": ["tenure"] if alert else [],
            "features": [{"feature": "tenure", "kind": "numeric", "algorithm": "psi",
                          "score": 0.7 if alert else 0.01, "threshold": 0.2, "drifted": alert}],
        }],
    }


def test_message_shows_alert_and_feature() -> None:
    text = build_message(_report(alert=True))
    assert "Drift detectado" in text and "tenure" in text


def test_webhook_is_called_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: List[str] = []
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/fake")
    monkeypatch.setattr(notify_main, "send_to_slack", lambda url, text: sent.append(text))
    result = notify_main.handler({"report": _report(alert=True)}, None)
    assert result["sent"] is True and len(sent) == 1


def test_only_on_alert_skips_quiet_days(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/fake")
    monkeypatch.setenv("NOTIFY_ONLY_ON_ALERT", "true")
    monkeypatch.setattr(notify_main, "send_to_slack", lambda url, text: pytest.fail("no debía enviar"))
    assert notify_main.handler({"report": _report(alert=False)}, None)["sent"] is False


@mock_aws
def test_s3_storage_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    """moto simula S3 en memoria: el test no toca AWS real ni necesita credenciales."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    boto3.client("s3").create_bucket(Bucket="bucket-de-prueba")
    monkeypatch.setenv("STORAGE", "s3")
    monkeypatch.setenv("DATA_BUCKET", "bucket-de-prueba")

    storage = get_storage()
    assert isinstance(storage, S3Storage)
    write_json(storage, "reports/x.json", {"ok": True})
    assert storage.exists("reports/x.json")
    assert not storage.exists("reports/otro.json")
    assert read_json(storage, "reports/x.json") == {"ok": True}


def test_s3_without_bucket_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE", "s3")
    monkeypatch.delenv("DATA_BUCKET", raising=False)
    with pytest.raises(RuntimeError, match="DATA_BUCKET"):
        get_storage()
