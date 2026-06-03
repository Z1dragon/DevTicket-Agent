from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from devticket_agent.agent import DevTicketAgent
from devticket_agent.metrics import MetricsRegistry
from devticket_agent.storage import TraceStore, trace_to_dict


app = FastAPI(
    title="DevTicket-Agent",
    description="A lightweight Agentic RAG assistant for developer ticket triage.",
    version="0.1.0",
)


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="研发工单或排障问题")


class AskResponse(BaseModel):
    trace_id: str
    answer: str
    category: str
    category_reason: str
    retrieved_docs: list[dict]
    tool_calls: list[dict]
    critic: dict
    trace_steps: list[dict]


metrics = MetricsRegistry()


@lru_cache(maxsize=1)
def get_agent() -> DevTicketAgent:
    return DevTicketAgent()


@lru_cache(maxsize=1)
def get_trace_store() -> TraceStore:
    return TraceStore()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <!doctype html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>DevTicket-Agent Demo</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f6f7f9; color: #172033; }
        main { max-width: 960px; margin: 0 auto; padding: 28px 16px 48px; }
        h1 { margin: 0 0 8px; }
        textarea { width: 100%; min-height: 96px; box-sizing: border-box; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; font-size: 15px; }
        button { margin-top: 10px; border: 0; border-radius: 8px; background: #2563eb; color: white; padding: 10px 14px; font-weight: 700; cursor: pointer; }
        section { background: white; border: 1px solid #d8dee8; border-radius: 8px; padding: 16px; margin-top: 16px; }
        pre { white-space: pre-wrap; word-break: break-word; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; }
      </style>
    </head>
    <body>
      <main>
        <h1>DevTicket-Agent</h1>
        <p>研发工单 Agentic RAG 助手：分类、检索、工具调用、critic、trace。</p>
        <section>
          <textarea id="query">订单创建接口最近总是 500，日志里有 DB_CONN_TIMEOUT，应该怎么排查？</textarea>
          <button onclick="ask()">Ask</button>
        </section>
        <section>
          <h2>结果</h2>
          <pre id="result">等待请求...</pre>
        </section>
      </main>
      <script>
        async function ask() {
          const query = document.getElementById('query').value;
          const res = await fetch('/ask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query})
          });
          document.getElementById('result').textContent = JSON.stringify(await res.json(), null, 2);
        }
      </script>
    </body>
    </html>
    """


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    trace = get_agent().run(request.query)
    get_trace_store().save(trace)
    total_duration = sum(step.duration_ms for step in trace.steps)
    metrics.record(trace.classification.category, trace.critic_result.risk_level, total_duration)
    return AskResponse(
        trace_id=trace.trace_id,
        answer=trace.answer,
        category=trace.classification.category,
        category_reason=trace.classification.reason,
        retrieved_docs=[
            {
                "id": doc.id,
                "title": doc.title,
                "score": doc.score,
            }
            for doc in trace.documents
        ],
        tool_calls=[
            {
                "name": tool.name,
                "input": tool.input,
                "output": tool.output,
            }
            for tool in trace.tool_results
        ],
        critic={
            "risk_level": trace.critic_result.risk_level,
            "should_escalate": trace.critic_result.should_escalate,
            "reasons": trace.critic_result.reasons,
            "suggested_next_step": trace.critic_result.suggested_next_step,
        },
        trace_steps=[
            {
                "name": step.name,
                "duration_ms": step.duration_ms,
                "metadata": step.metadata,
            }
            for step in trace.steps
        ],
    )


@app.get("/traces")
def list_traces(limit: int = 20) -> list[dict]:
    return get_trace_store().list_recent(limit=limit)


@app.get("/traces/{trace_id}")
def get_trace(trace_id: str) -> dict:
    trace = get_trace_store().get(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return trace


@app.get("/metrics", response_class=PlainTextResponse)
def get_metrics() -> str:
    agent = get_agent()
    body = metrics.as_prometheus()
    body += f"devticket_retriever_cache_hits_total {agent.retriever.cache_hits}\n"
    body += f"devticket_retriever_cache_misses_total {agent.retriever.cache_misses}\n"
    return body
