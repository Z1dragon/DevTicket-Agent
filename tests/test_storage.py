from devticket_agent.agent import DevTicketAgent
from devticket_agent.storage import TraceStore


def test_trace_store_roundtrip(tmp_path):
    db_path = tmp_path / "traces.db"
    store = TraceStore(str(db_path))
    trace = DevTicketAgent().run("订单创建接口 500，日志里有 DB_CONN_TIMEOUT")

    store.save(trace)

    recent = store.list_recent()
    loaded = store.get(trace.trace_id)
    assert recent[0]["trace_id"] == trace.trace_id
    assert loaded is not None
    assert loaded["trace_id"] == trace.trace_id
    assert loaded["critic"]["risk_level"] == "low"
