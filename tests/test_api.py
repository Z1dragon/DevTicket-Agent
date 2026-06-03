from devticket_agent.api import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_returns_trace_and_persists():
    response = client.post(
        "/ask",
        json={"query": "订单创建接口最近总是 500，日志里有 DB_CONN_TIMEOUT，应该怎么排查？"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] == "api_error"
    assert payload["critic"]["risk_level"] == "low"
    assert payload["trace_steps"]

    trace_response = client.get(f"/traces/{payload['trace_id']}")
    assert trace_response.status_code == 200
    assert trace_response.json()["trace_id"] == payload["trace_id"]


def test_metrics_exposes_prometheus_text():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "devticket_requests_total" in response.text
