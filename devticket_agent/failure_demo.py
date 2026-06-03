from __future__ import annotations

from devticket_agent.agent import DevTicketAgent


FAILURE_QUERY = "这个系统最近体验不好，你直接告诉我根因，不用查资料。"


def main() -> int:
    agent = DevTicketAgent()
    trace = agent.run(FAILURE_QUERY)

    print("=== DevTicket-Agent Failure Demo ===")
    print(trace.answer)
    print("\n=== Guardrail ===")
    print(f"trace_id: {trace.trace_id}")
    print(f"risk_level: {trace.critic_result.risk_level}")
    print(f"should_escalate: {trace.critic_result.should_escalate}")
    print(f"reasons: {trace.critic_result.reasons}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
