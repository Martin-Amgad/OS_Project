"""SJF scheduler implementation (preemptive and non-preemptive)."""
from typing import Any, Dict

from ...base_scheduler import BaseScheduler
from ....models import Process


class SJFScheduler(BaseScheduler):
    def __init__(self, processes: list[Process], preemptive: bool = False) -> None:
        super().__init__(processes)
        self.preemptive = preemptive

    def get_algorithm_name(self) -> str:
        return "SJF (Preemptive)" if self.preemptive else "SJF (Non-Preemptive)"

    def tick(self) -> Dict[str, Any]:
        # 1) Add newly arrived processes at current_time to ready queue
        self._check_arrivals()

        if self.preemptive:
            # 2a) Preemptive SJF (SRTF): choose shortest remaining time
            candidates: list[Process] = []

            if self.current_process is not None and not self.current_process.is_completed:
                candidates.append(self.current_process)

            for p in self.ready_queue:
                if not p.is_completed:
                    candidates.append(p)

            if candidates:
                chosen = min(
                    candidates,
                    key=lambda p: (p.remaining_time, p.arrival_time, p.pid)
                )

                if chosen is not self.current_process:
                    # Preempt currently running process (if any)
                    if self.current_process is not None and not self.current_process.is_completed:
                        self.current_process.preemption_count += 1
                        self.ready_queue.append(self.current_process)

                    # Remove chosen from ready queue if it is there, then start it
                    if chosen in self.ready_queue:
                        self.ready_queue.remove(chosen)

                    self._start_new_process(chosen)

        else:
            # 2b) Non-preemptive SJF: choose only when CPU is idle
            if self.current_process is None and self.ready_queue:
                chosen = min(
                    self.ready_queue,
                    key=lambda p: (p.burst_time, p.arrival_time, p.pid)
                )
                self.ready_queue.remove(chosen)
                self._start_new_process(chosen)

        # 3) Execute current process for one time unit (or idle if None)
        self._execute_current_process()

        # 4) Advance simulation time
        self.current_time += 1

        # 5) Return standardized GUI state dict
        return self._get_return_dict()