from __future__ import annotations

from devticket_agent.classifier import Classification
from devticket_agent.critic import CriticResult
from devticket_agent.retriever import RetrievedDocument
from devticket_agent.tools import ToolResult


def generate_answer(
    query: str,
    classification: Classification,
    documents: list[RetrievedDocument],
    tool_results: list[ToolResult],
    critic_result: CriticResult | None = None,
) -> str:
    evidence_lines = [f"- {doc.title} ({doc.id}, score={doc.score})" for doc in documents]
    tool_lines = [f"- {tool.name}({tool.input}): {tool.output}" for tool in tool_results]
    critic_lines = _format_critic(critic_result)

    if not documents and not tool_results:
        return (
            "结论：当前证据不足，建议升级人工或补充日志、错误码和业务上下文。\n"
            f"分类：{classification.category}，原因：{classification.reason}"
        )

    actions = _build_actions(classification.category)
    return "\n".join(
        [
            f"工单问题：{query}",
            f"分类：{classification.category}（{classification.reason}）",
            "检索证据：",
            *(evidence_lines or ["- 未检索到高相关文档"]),
            "工具结果：",
            *(tool_lines or ["- 本轮不需要调用外部工具"]),
            "处理建议：",
            *[f"{index}. {action}" for index, action in enumerate(actions, start=1)],
            "自检结果：",
            *critic_lines,
            "置信度说明：回答仅基于检索证据和工具数据源结果；证据不足时应升级人工确认。",
        ]
    )


def _format_critic(critic_result: CriticResult | None) -> list[str]:
    if critic_result is None:
        return ["- 未启用 critic"]
    reasons = "；".join(critic_result.reasons)
    return [
        f"- risk_level={critic_result.risk_level}, should_escalate={critic_result.should_escalate}",
        f"- reasons={reasons}",
        f"- next_step={critic_result.suggested_next_step}",
    ]


def _build_actions(category: str) -> list[str]:
    if category == "api_error":
        return ["先确认错误码含义和影响范围", "查看服务状态、连接池和最近发布记录", "给出临时降级或重试方案"]
    if category == "rag_quality":
        return ["检查 chunk 切分、metadata filter 和 embedding 索引", "对比召回结果与期望文档", "加入 rerank 或调整上下文注入策略"]
    if category == "performance":
        return ["先看 p95、error rate、CPU、内存和下游依赖", "结合日志定位慢查询、队列堆积或连接池瓶颈", "必要时启用缓存或降级"]
    if category == "security":
        return ["隔离用户输入、系统指令和检索证据", "限制工具 allowlist 和敏感操作权限", "记录异常提示词并加入评测 case"]
    return ["补充日志、错误码和上下游信息", "检索已有 runbook", "低置信度时升级人工"]
