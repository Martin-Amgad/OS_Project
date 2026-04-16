"""Placeholder file for Priority scheduler."""


from typing import Dict, Any
from ...models import Process
from ...scheduler.base_scheduler import BaseScheduler

class PriorityScheduler(BaseScheduler):
    
    def __init__(self, processes: list[Process], preemptive: bool = False) -> None:
        super().__init__(processes)
        self.preemptive = preemptive

    def get_algorithm_name(self) -> str:
        return "Priority Scheduling (Preemptive) "  if self.preemptive else "Priority Scheduling (Non-Preemptive)"

    def tick(self) -> Dict[str, Any]:
        """
        This method is called by the GUI every 1 second.
        It must advance the simulation by exactly ONE unit of time.
        """
        # 1. Check for new process arrivals at the current time
        # This is provided by the BaseScheduler
        self._check_arrivals()
        
        # 2. Apply Scheduling Policy (Selection Logic)
        if self.preemptive:
            # PREEMPTIVE: always check if a higher priority process is available to run
            if self.ready_queue:
                # Select process with highest priority (smallest priority number)
                # This is where the 'Preemptive' logic happens every tick
                highest_priority_process = min(self.ready_queue, key=lambda p: p.priority)

                # If the CPU is idle, or if a higher priority process just arrived
                if self.current_process is None or highest_priority_process.priority < self.current_process.priority:
                    
                    # If a lower priority process was running, put it back in the ready queue
                    if self.current_process is not None:
                        self.ready_queue.append(self.current_process)
                    
                    # Start the new highest priority process
                    # Remove it from ready queue and set as current
                    self.ready_queue.remove(highest_priority_process)
                    self._start_new_process(highest_priority_process)

        else:
            # Non-preemptive: only select a new process if CPU is idle
            if self.current_process is None and self.ready_queue:
                highest_priority_process = min(
                    self.ready_queue, key=lambda p: p.priority
                )
                self.ready_queue.remove(highest_priority_process)
                self._start_new_process(highest_priority_process)

        # 3. Execute the current process for 1 unit of time
        # This updates remaining_time and Gantt chart
        self._execute_current_process()

        # 4. If nothing is running and nothing is in the queue, the CPU is idle
        # The current_time is incremented after each tick
        self.current_time += 1

        # 5. Return the standardized dictionary for the GUI to update
        return self._get_return_dict()