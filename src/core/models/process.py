from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Process:
    pid: str
    arrival_time: int
    burst_time: int
    priority: int = 0
    remaining_time: int = field(init=False)
    completion_time: int | None = None
    insertion_index: int = 0

    def __post_init__(self) -> None:
        self.remaining_time = self.burst_time
