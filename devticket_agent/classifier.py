from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Classification:
    category: str
    reason: str


KEYWORDS = {
    "rag_quality": ["rag", "召回", "向量", "检索", "rerank", "chunk", "知识库", "vector"],
    "performance": ["p95", "延迟", "变慢", "性能", "cpu", "队列", "慢查询", "耗时"],
    "security": ["prompt injection", "忽略系统", "越权", "注入", "安全", "泄露"],
    "api_error": ["500", "错误码", "timeout", "超时", "接口", "登录态", "auth", "upstream"],
}


def classify_ticket(query: str) -> Classification:
    normalized = query.lower()
    scores: dict[str, int] = {}

    for category, keywords in KEYWORDS.items():
        scores[category] = sum(1 for keyword in keywords if keyword.lower() in normalized)

    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        return Classification(category="unknown", reason="没有命中明确的工单类型关键词")

    reason = f"命中 {best_category} 相关关键词 {scores[best_category]} 个"
    return Classification(category=best_category, reason=reason)
