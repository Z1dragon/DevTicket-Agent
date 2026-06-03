from __future__ import annotations

from devticket_agent.agent import DevTicketAgent


DEMO_QUERY = "订单创建接口最近总是 500，日志里有 DB_CONN_TIMEOUT，应该怎么排查？"


def main() -> int:
    agent = DevTicketAgent()
    trace = agent.run(DEMO_QUERY)

    print("=== DevTicket-Agent Demo ===")
    print(trace.answer)
    print("\n=== Trace ===")
    print(f"trace_id: {trace.trace_id}")
    print(f"category: {trace.classification.category}")
    print(f"docs: {[doc.id for doc in trace.documents]}")
    print(f"tools: {[tool.name for tool in trace.tool_results]}")
    print(f"critic: {trace.critic_result.risk_level}, escalate={trace.critic_result.should_escalate}")
    for step in trace.steps:
        print(f"- {step.name}: {step.duration_ms}ms {step.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
