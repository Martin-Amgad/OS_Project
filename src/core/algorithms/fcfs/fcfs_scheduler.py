"""
This module implements the FCFS scheduling algorithm.
Processes are executed in the exact order they arrive.

Characteristics:
- Non-preemptive (once a process starts, it runs until completion)
- Simple FIFO queue management
- Convoy effect possible (short processes wait behind long processes)
"""

from typing import Dict, Any
from ...models import Process
from ...scheduler.base_scheduler import BaseScheduler

class FCFSScheduler(BaseScheduler):

    def get_algorithm_name(self) -> str:
        return "FCFS (First Come First Served)"
    
    def tick(self) -> Dict[str, Any]:
        
        # Early return if simulation is already finished
        if self.is_finished:
            return self._get_return_dict()   
            
        # Check for new process arrivals at current time
        # This adds any processes with arrival_time == current_time
        # to the ready queue in the order they appear in self.processes
        self._check_arrivals()
        
        # Select next process if CPU is idle
        # FCFS Policy: Always select the first process in the ready queue
        if self.current_process is None and self.ready_queue:
            # pop(0) removes and returns the first element (FIFO behavior)
            next_process = self.ready_queue.pop(0)
            self._start_new_process(next_process)
        
        # Execute the current process for 1 time unit
        self._execute_current_process()
   
        # Increment simulation time
        self.current_time += 1
        
        # Return updated state for GUI
        return self._get_return_dict()