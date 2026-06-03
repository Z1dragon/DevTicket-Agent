from __future__ import annotations

from dataclasses import dataclass

from devticket_agent.classifier import Classification, classify_ticket
from devticket_agent.critic import CriticResult, review_answer
from devticket_agent.generator import generate_answer
from devticket_agent.observability import TraceRecorder, TraceStep
from devticket_agent.retriever import KeywordRetriever, RetrievedDocument
from devticket_agent.tools import ToolBox, ToolResult, choose_tools


@dataclass(frozen=True)
class AgentTrace:
    trace_id: str
    query: str
    classification: Classification
    documents: list[RetrievedDocument]
    tool_results: list[ToolResult]
    critic_result: CriticResult
    answer: str
    steps: list[TraceStep]


class DevTicketAgent:
    def __init__(self) -> None:
        self.retriever = KeywordRetriever()
        self.toolbox = ToolBox()

    def run(self, query: str) -> AgentTrace:
        recorder = TraceRecorder()

        with recorder.step("classify") as metadata:
            classification = classify_ticket(query)
            metadata["category"] = classification.category
            metadata["reason"] = classification.reason

        with recorder.step("retrieve") as metadata:
            documents = self.retriever.search(query)
            metadata["doc_ids"] = [doc.id for doc in documents]
            metadata["top_score"] = documents[0].score if documents else 0

        with recorder.step("tool_call") as metadata:
            tool_results = choose_tools(classification.category, query, self.toolbox)
            metadata["tool_names"] = [tool.name for tool in tool_results]

        with recorder.step("critic") as metadata:
            critic_result = review_answer(classification, documents, tool_results)
            metadata["risk_level"] = critic_result.risk_level
            metadata["should_escalate"] = critic_result.should_escalate
            metadata["reasons"] = critic_result.reasons

        with recorder.step("generate") as metadata:
            answer = generate_answer(query, classification, documents, tool_results, critic_result)
            metadata["answer_chars"] = len(answer)

        return AgentTrace(
            trace_id=recorder.trace_id,
            query=query,
            classification=classification,
            documents=documents,
            tool_results=tool_results,
            critic_result=critic_result,
            answer=answer,
            steps=recorder.steps,
        )
