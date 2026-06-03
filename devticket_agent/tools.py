from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from devticket_agent.io_utils import load_json


@dataclass(frozen=True)
class ToolResult:
    name: str
    input: str
    output: str


class ToolBox:
    def __init__(
        self,
        error_codes_path: str = "data/error_codes.json",
        service_status_path: str = "data/service_status.json",
        logs_path: str = "data/mock_logs.json",
    ) -> None:
        self.error_codes: dict[str, dict[str, Any]] = load_json(error_codes_path)
        self.service_status_data: dict[str, dict[str, Any]] = load_json(service_status_path)
        self.logs: dict[str, list[str]] = load_json(logs_path)

    def error_code_lookup(self, query: str) -> ToolResult | None:
        for code, detail in self.error_codes.items():
            if code.lower() in query.lower():
                causes = "、".join(detail["likely_causes"])
                actions = "；".join(detail["suggested_actions"])
                output = f"{detail['meaning']}。常见原因：{causes}。建议动作：{actions}。"
                return ToolResult(name="error_code_lookup", input=code, output=output)
        return None

    def service_status(self, query: str) -> ToolResult:
        service = select_service(query)
        status = self.service_status_data[service]
        output = ", ".join(f"{key}={value}" for key, value in status.items())
        return ToolResult(name="service_status", input=service, output=output)

    def log_search(self, query: str) -> ToolResult:
        service = select_service(query)
        lines = self.logs.get(service, ["No critical error found in the latest logs."])
        return ToolResult(name="log_search", input=service, output=" | ".join(lines[:3]))


def select_service(query: str) -> str:
    service = "order-service"
    if "rag" in query.lower() or "向量" in query or "检索" in query:
        service = "rag-service"
    if "auth" in query.lower() or "登录" in query:
        service = "auth-service"
    return service


def choose_tools(category: str, query: str, toolbox: ToolBox | None = None) -> list[ToolResult]:
    toolbox = toolbox or ToolBox()
    results: list[ToolResult] = []

    code_result = toolbox.error_code_lookup(query)
    if code_result:
        results.append(code_result)

    if category in {"api_error", "performance"}:
        results.append(toolbox.service_status(query))

    if category == "performance":
        results.append(toolbox.log_search(query))

    return results
