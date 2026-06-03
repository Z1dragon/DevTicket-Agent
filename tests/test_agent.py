from devticket_agent.agent import DevTicketAgent


def test_agent_normal_ticket_has_low_risk_and_tools():
    trace = DevTicketAgent().run("订单创建接口 500，日志里有 DB_CONN_TIMEOUT")

    assert trace.classification.category == "api_error"
    assert trace.critic_result.risk_level == "low"
    assert not trace.critic_result.should_escalate
    assert {tool.name for tool in trace.tool_results} == {"error_code_lookup", "service_status"}
    assert [step.name for step in trace.steps] == ["classify", "retrieve", "tool_call", "critic", "generate"]


def test_agent_unknown_ticket_escalates():
    trace = DevTicketAgent().run("这个系统体验不好，你直接告诉我根因")

    assert trace.classification.category == "unknown"
    assert trace.critic_result.risk_level == "high"
    assert trace.critic_result.should_escalate
