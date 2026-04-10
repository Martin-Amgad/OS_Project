"""
This module defines the Process class which represents a single process
in the CPU scheduling simulation. It tracks all necessary attributes
for scheduling algorithms including FCFS, SJF, Round Robin, and Priority.
"""

from typing import List, Optional, Dict

class Process:
    """Represents a single process in the simulation."""
    
    def __init__(
        self,
        pid: str,
        arrival_time: int,
        burst_time: int,
        priority: Optional[int] = None
        ):
        
        # Validate values
        if arrival_time < 0:
            raise ValueError(f"arrival_time must be >= 0, got {arrival_time}")
        if burst_time <= 0:
            raise ValueError(f"burst_time must be > 0, got {burst_time}")
        
        
        # Core Process Attributes (Static/Immutable)
        self.pid: str = pid                         # Process identifier - unique name for this process
        self.arrival_time: int = arrival_time       # Time unit when process enters system
        self.burst_time: int = burst_time           # Total CPU time required (original value, never changes)
    
        # Priority - for priority scheduling algorithms
        # Type: Optional[int], None means no priority assigned
        # Note: Lower value typically means higher priority
        self.priority: Optional[int] = priority    
        
        
        # Dynamic Process Attributes (Change during simulation)
        self.remaining_time: int = burst_time       # CPU time still needed to complete (decrements during execution)
        self.is_completed: bool = False             # Flag for quick completion checking

        
        # Statistics (calculated when process finishes)
        self.completion_time: Optional[int] = None  # Time when process finishes execution, None until completion
        self.turnaround_time: Optional[int] = None  # Total time from arrival to completion, calculated as completion_time - arrival_time
        self.waiting_time: Optional[int] = None     # Time spent waiting in ready queue, calculated as turnaround_time - burst_time
        self.first_response_time: Optional[int] = None  # Time until first CPU allocation, calculated as start_time - arrival_time

        
        # Execution Tracking
        self.start_time: Optional[int] = None      # First time this process ever received CPU, None until first execution
        self.preemption_count: int = 0             # Number of times this process has been preempted
        
        # Execution history - record of when process ran on CPU
        # List of {start: int, end: int}
        self.execution_history: List[Dict[str, int]] = []  
        
    def to_dict(self):
        """Returns a dictionary for displaying in GUI table."""
        return {
            # Core attributes
            'PID': self.pid,
            'Arrival': self.arrival_time,
            'Burst': self.burst_time,
            'Remaining': self.remaining_time,
            'Priority': self.priority if self.priority is not None else '-',
            
            # Statistics (only show if available)
            'Completion': self.completion_time if self.completion_time is not None else '-',
            'Turnaround': self.turnaround_time if self.turnaround_time is not None else '-',
            'Waiting': self.waiting_time if self.waiting_time is not None else '-',
            'Response': self.first_response_time if self.first_response_time is not None else '-',
            
            # Additional metrics
            'Preemptions': self.preemption_count,
        }
    
    def __repr__(self):
        return (f"Process(pid='{self.pid}', "
                f"arrival={self.arrival_time}, "
                f"burst={self.burst_time}, "
                f"remaining={self.remaining_time}, "
                f"priority={self.priority} ")