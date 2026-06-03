from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass(frozen=True)
class TraceStep:
    name: str
    duration_ms: float
    metadata: dict[str, Any]


@dataclass
class TraceRecorder:
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    steps: list[TraceStep] = field(default_factory=list)

    @contextmanager
    def step(self, name: str) -> Iterator[dict[str, Any]]:
        metadata: dict[str, Any] = {}
        started_at = time.perf_counter()
        try:
            yield metadata
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
            self.steps.append(TraceStep(name=name, duration_ms=duration_ms, metadata=metadata))
