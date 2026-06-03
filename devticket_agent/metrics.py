from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MetricsRegistry:
    request_count: int = 0
    category_counts: dict[str, int] = field(default_factory=dict)
    risk_counts: dict[str, int] = field(default_factory=dict)
    total_duration_ms: float = 0.0

    def record(self, category: str, risk_level: str, duration_ms: float) -> None:
        self.request_count += 1
        self.category_counts[category] = self.category_counts.get(category, 0) + 1
        self.risk_counts[risk_level] = self.risk_counts.get(risk_level, 0) + 1
        self.total_duration_ms += duration_ms

    def as_prometheus(self) -> str:
        lines = [
            "# HELP devticket_requests_total Total /ask requests handled.",
            "# TYPE devticket_requests_total counter",
            f"devticket_requests_total {self.request_count}",
            "# HELP devticket_request_duration_ms_avg Average request duration in milliseconds.",
            "# TYPE devticket_request_duration_ms_avg gauge",
            f"devticket_request_duration_ms_avg {self.average_duration_ms():.3f}",
        ]
        for category, count in sorted(self.category_counts.items()):
            lines.append(f'devticket_requests_by_category_total{{category="{category}"}} {count}')
        for risk, count in sorted(self.risk_counts.items()):
            lines.append(f'devticket_requests_by_risk_total{{risk_level="{risk}"}} {count}')
        return "\n".join(lines) + "\n"

    def average_duration_ms(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.total_duration_ms / self.request_count
