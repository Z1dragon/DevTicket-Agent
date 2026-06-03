from __future__ import annotations

from dataclasses import dataclass

from devticket_agent.classifier import Classification
from devticket_agent.retriever import RetrievedDocument
from devticket_agent.tools import ToolResult


@dataclass(frozen=True)
class CriticResult:
    risk_level: str
    should_escalate: bool
    reasons: list[str]
    suggested_next_step: str


def review_answer(
    classification: Classification,
    documents: list[RetrievedDocument],
    tool_results: list[ToolResult],
) -> CriticResult:
    reasons: list[str] = []
    top_score = documents[0].score if documents else 0

    if classification.category == "unknown":
        reasons.append("工单类型未明确识别")

    if not documents:
        reasons.append("没有检索到可引用知识文档")
    elif top_score < 0.12:
        reasons.append(f"最高检索分数较低：{top_score}")

    if classification.category in {"api_error", "performance"} and not tool_results:
        reasons.append("需要排障工具但本轮未调用任何工具")

    if classification.category == "security":
        reasons.append("安全类问题需要人工复核策略边界")

    if not reasons:
        return CriticResult(
            risk_level="low",
            should_escalate=False,
            reasons=["分类、检索证据和工具调用满足当前回答条件"],
            suggested_next_step="可以基于当前证据给出排查建议，并保留 trace 便于复盘。",
        )

    risk_level = "high" if classification.category == "unknown" or not documents else "medium"
    return CriticResult(
        risk_level=risk_level,
        should_escalate=risk_level == "high",
        reasons=reasons,
        suggested_next_step="补充日志、错误码、服务名或业务上下文；高风险场景建议升级人工确认。",
    )
