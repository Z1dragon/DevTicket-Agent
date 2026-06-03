from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from devticket_agent.agent import AgentTrace


class TraceStore:
    def __init__(self, db_path: str = "data/devticket_traces.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    category TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    should_escalate INTEGER NOT NULL,
                    answer TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def save(self, trace: AgentTrace) -> None:
        payload = trace_to_dict(trace)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO traces (
                    trace_id, query, category, risk_level, should_escalate, answer, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.trace_id,
                    trace.query,
                    trace.classification.category,
                    trace.critic_result.risk_level,
                    int(trace.critic_result.should_escalate),
                    trace.answer,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT trace_id, query, category, risk_level, should_escalate, created_at
                FROM traces
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, trace_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload_json FROM traces WHERE trace_id = ?", (trace_id,)).fetchone()
        if row is None:
            return None
        return json.loads(row[0])


def trace_to_dict(trace: AgentTrace) -> dict[str, Any]:
    return {
        "trace_id": trace.trace_id,
        "query": trace.query,
        "answer": trace.answer,
        "category": trace.classification.category,
        "category_reason": trace.classification.reason,
        "retrieved_docs": [
            {"id": doc.id, "title": doc.title, "score": doc.score, "content": doc.content}
            for doc in trace.documents
        ],
        "tool_calls": [
            {"name": tool.name, "input": tool.input, "output": tool.output}
            for tool in trace.tool_results
        ],
        "critic": {
            "risk_level": trace.critic_result.risk_level,
            "should_escalate": trace.critic_result.should_escalate,
            "reasons": trace.critic_result.reasons,
            "suggested_next_step": trace.critic_result.suggested_next_step,
        },
        "trace_steps": [
            {"name": step.name, "duration_ms": step.duration_ms, "metadata": step.metadata}
            for step in trace.steps
        ],
    }
