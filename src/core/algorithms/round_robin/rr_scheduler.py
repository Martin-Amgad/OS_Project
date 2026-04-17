"""
This module implements the Round Robin scheduling algorithm.
Processes are executed in circular order with a fixed time quantum.

Characteristics:
- Preemptive (processes are interrupted when quantum expires)
- Circular FIFO queue management
- Fair CPU distribution among all processes
"""

from typing import Dict, Any
from ...models import Process
from ...scheduler.base_scheduler import BaseScheduler


class RoundRobinScheduler(BaseScheduler):
    """Round Robin Scheduler with configurable time quantum."""
    
    def __init__(self, processes: list[Process], quantum: int = 2) -> None:
        if quantum <= 0:
            raise ValueError("quantum must be a positive integer")
        
        super().__init__(processes)
        self.quantum = quantum
        self.time_slice_remaining = 0
    
    def get_algorithm_name(self) -> str:
        return f"Round Robin (q={self.quantum})"
    
    def tick(self) -> Dict[str, Any]:
        if self.is_finished:
            return self._get_return_dict()

        # 1. Add arrivals
        self._check_arrivals()

        # 2. Handle quantum expiration BEFORE execution
        if (self.current_process is not None and 
            self.time_slice_remaining == 0):

            self.current_process.preemption_count += 1
            self.ready_queue.append(self.current_process)
            self.current_process = None

        # 3. If CPU idle → schedule next
        if self.current_process is None and self.ready_queue:
            next_process = self.ready_queue.pop(0)
            self._start_new_process(next_process)
            self.time_slice_remaining = self.quantum

        # 4. Execute
        process_finished = False
        if self.current_process is not None:
            process_finished = self._execute_current_process()
            self.time_slice_remaining -= 1

        # 5. Advance time
        self.current_time += 1

        # 6. Handle completion ONLY
        if process_finished:
            self.current_process = None


        return self._get_return_dict()