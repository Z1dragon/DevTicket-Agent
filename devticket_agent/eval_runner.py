from __future__ import annotations

from dataclasses import dataclass

from devticket_agent.agent import DevTicketAgent, AgentTrace
from devticket_agent.io_utils import load_json


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    category_ok: bool
    doc_hit: bool
    tool_hit: bool
    score: float


def evaluate_case(case: dict, trace: AgentTrace) -> CaseResult:
    actual_doc_ids = {doc.id for doc in trace.documents}
    actual_tools = {tool.name for tool in trace.tool_results}
    expected_doc_ids = set(case["expected_doc_ids"])
    expected_tools = set(case["expected_tools"])

    category_ok = trace.classification.category == case["expected_category"]
    doc_hit = bool(actual_doc_ids & expected_doc_ids)
    tool_hit = expected_tools.issubset(actual_tools)
    score = round((category_ok + doc_hit + tool_hit) / 3, 3)

    return CaseResult(
        case_id=case["id"],
        category_ok=category_ok,
        doc_hit=doc_hit,
        tool_hit=tool_hit,
        score=score,
    )


def main() -> int:
    agent = DevTicketAgent()
    cases = load_json("data/eval_cases.json")
    results: list[CaseResult] = []

    for case in cases:
        trace = agent.run(case["query"])
        results.append(evaluate_case(case, trace))

    print("case_id,category_ok,doc_hit,tool_hit,score")
    for result in results:
        print(
            f"{result.case_id},"
            f"{result.category_ok},"
            f"{result.doc_hit},"
            f"{result.tool_hit},"
            f"{result.score}"
        )

    avg_score = sum(result.score for result in results) / max(len(results), 1)
    print(f"\naverage_score={avg_score:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
