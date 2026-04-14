"""
base_scheduler.py - Abstract Base Class for CPU Scheduling Algorithms

This module defines the BaseScheduler abstract class which serves as the
interface that ALL scheduling algorithms must implement. It provides common
functionality for process management, time tracking, and statistics calculation.

The GUI will ONLY interact with schedulers through the methods defined here,
ensuring consistent behavior across FCFS, SJF, Round Robin, and Priority schedulers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from ..models import Process

class BaseScheduler(ABC):
    
    def __init__(self, processes: List[Process]) -> None:
        
        # ---- Input Validation ----    
        if not isinstance(processes, list):
            raise TypeError(f"processes must be a list, got {type(processes).__name__}")
        
        if not processes:
            raise ValueError("processes list cannot be empty")
        
        for i, p in enumerate(processes):
            if not isinstance(p, Process):
                raise TypeError(f"Item at index {i} is not a Process object: {type(p).__name__}")
            
        # Create DEEP COPIES of all processes so original data isn't modified
        self.processes: List[Process] = []
        for original_process in processes:
            # Create a new Process instance with the same attributes
            cloned_process = Process(
                pid=original_process.pid,
                arrival_time=original_process.arrival_time,
                burst_time=original_process.burst_time,
                priority=original_process.priority
            )
            self.processes.append(cloned_process)
        
        # Sort by arrival time (important for checking arrivals in order)
        self.processes.sort(key=lambda p: p.arrival_time)
        
        # ---- Time Management ----     
        self.current_time: int = 0     # Current simulation time (starts at 0)
        
        # ---- Process Tracking Data Structures ----
        self.current_process: Optional[Process] = None   # Currently executing process on CPU (None if CPU is idle)
        self.ready_queue: List[Process] = []             # List of Process objects waiting for CPU
        self.completed_queue: List[Process] = []         # List of Completed processes - in order of completion
        self.arrived_processes: Set[str] = set()         # Set of PIDs that have already been added to ready queue (to prevent duplicates)
        
        # ---- Gantt Chart Data Structure ----
        # Gantt chart records CPU allocation timeline
        # List of dicts: {'pid': str, 'start': int, 'end': int}
        self.gantt_chart: List[Dict[str, Any]] = []   
        
        # ---- Simulation State ----
        self.is_finished: bool = False                   # Flag for quick completion checking
    
    # ---- ABSTRACT METHODS (MUST BE IMPLEMENTED BY SUBCLASSES) ----
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """Returns the name of the scheduling algorithm as a string."""
        pass
    
    @abstractmethod
    def tick(self) -> Dict[str, Any]:
        """
        Advance the simulation by ONE time unit.
        
        This is the core method that implements the scheduling algorithm.
        It is called repeatedly (e.g., every 1 second by GUI timer) to
        simulate the passage of time.
        
        Each tick should:
        1. Check for new process arrivals at current_time
        2. Apply scheduling policy to select/switch processes
        3. Execute the current process for 1 time unit
        4. Update all tracking data structures
        5. Check for completion conditions
        6. Increment current_time
        
        Returns:
            Dict[str, Any]: Complete state information for GUI update
                Must include:
                - 'current_time': int
                - 'current_pid': Optional[str]
                - 'ready_queue_pids': List[str]
                - 'processes_table': List[Dict]
                - 'gantt_chart': List[Dict]
                - 'avg_waiting': float
                - 'avg_turnaround': float
                - 'is_finished': bool
        """
        pass
    
    # ---- CORE FUNCTIONALITY METHODS ----   
    def _check_arrivals(self) -> List[Process]:
        """Check for processes arriving at current_time and add to ready queue."""
        arrived_processes: List[Process] = []
        for process in self.processes:
            if (process.arrival_time == self.current_time and 
                not process.is_completed and 
                process.pid not in self.arrived_processes):
                
                self.ready_queue.append(process)            # Add to ready queue
                self.arrived_processes.add(process.pid)     # Track that this process has arrived
                arrived_processes.append(process)           # Add to return list
                print(f"[Time {self.current_time}] Process {process.pid} arrived")
                
        return arrived_processes
    
    def _start_new_process(self, process: Process) -> None:
        """Set a process as current and record Gantt chart segment."""
        if process is None:
            raise ValueError("Cannot start None process")
        
        if process.is_completed:
            raise ValueError(f"Cannot start completed process: {process.pid}")
        
        self.current_process = process
        if self.current_process.start_time is None:
            self.current_process.start_time = self.current_time
            # Calculate first response time
            self.current_process.first_response_time = (
                self.current_time - self.current_process.arrival_time
            )
        
        # Create new segment in Gantt chart
        self.gantt_chart.append({
            'pid': self.current_process.pid,
            'start': self.current_time,
            'end': self.current_time  # Will extend each tick
        })
        
        # Add to execution history for this process
        self.current_process.execution_history.append({
            'start': self.current_time,
            'end': self.current_time  # Will be updated during execution
        })
        
        print(f"[Time {self.current_time}] Started executing {process.pid}")
    
    def _execute_current_process(self) -> bool:
        """Run current process for 1 time unit. Return True if it finished."""
        # If no process is running or current process is already completed, CPU is idle
        if self.current_process is None or self.current_process.is_completed:
            return False
        
        self.current_process.remaining_time -= 1                # Execute for 1 time unit
        self.gantt_chart[-1]['end'] = self.current_time + 1     # Update Gantt chart end time
        self.current_process.execution_history[-1]['end'] = self.current_time + 1  # Update execution history end time
        
        if self.current_process.remaining_time == 0:
            self._complete_current_process()
            return True
        return False
    
    def _complete_current_process(self) -> None:
        """Mark current process as complete and calculate statistics."""
        process  = self.current_process
        process .is_completed = True   
        process.completion_time = self.current_time + 1
        process.turnaround_time = process.completion_time - process.arrival_time
        process.waiting_time = process.turnaround_time - process.burst_time    
        self.completed_queue.append(process) 
        self.current_process = None
        
        print(f"[Time {process.completion_time}] Process {process.pid} COMPLETED")
        print(f"    Turnaround: {process.turnaround_time}, "
                f"Waiting: {process.waiting_time}, "
                f"Response: {process.first_response_time}")
    
    def _check_completion(self) -> bool:
        """Check if the entire simulation is complete."""

        # Check if all processes are completed
        all_completed = all(process.is_completed for process in self.processes)
        
        # Check CPU and ready queue status
        cpu_idle = self.current_process is None
        ready_queue_empty = len(self.ready_queue) == 0
        
        # Simulation is complete when all conditions are met
        is_complete = all_completed and cpu_idle and ready_queue_empty
        
        if is_complete:
            self.is_finished = True
        
        return is_complete

    # ---- DYNAMIC PROCESS MANAGEMENT ----
    def add_dynamic_process(self, process: Process) -> None:
        """Add a new process while simulation is running."""
        # Reopen the scheduler if it had reached a finished state.
        self.is_finished = False

        new_process = Process(process.pid, process.arrival_time, 
                       process.burst_time, process.priority)
        self.processes.append(new_process)
        self.processes.sort(key=lambda p: p.arrival_time)
        
        # If the process arrives at or before current time, add it immediately
        if new_process.arrival_time <= self.current_time:
            # Only add if not already completed
            if not new_process.is_completed and new_process.pid not in self.arrived_processes:
                self.ready_queue.append(new_process)
                self.arrived_processes.add(new_process.pid)
                
        print(f"[Time {self.current_time}] Dynamic process added: {new_process}")
        
    # ---- STATISTICS CALCULATION METHODS ----
    def calculate_statistics(self) -> tuple[float, float]:
        """Calculate average waiting and turnaround times."""
        if not self.completed_queue:
            return 0.0, 0.0
        
        # Sum up waiting times and turnaround times
        total_waiting: int = sum(
            p.waiting_time for p in self.completed_queue 
            if p.waiting_time is not None
        )
        total_turnaround: int = sum(
            p.turnaround_time for p in self.completed_queue 
            if p.turnaround_time is not None
        )
        n = len(self.completed_queue)
        
        # Calculate averages and round to 2 decimal places
        avg_waiting: float = round(total_waiting / n, 2)
        avg_turnaround: float = round(total_turnaround / n, 2)
        
        return avg_waiting, avg_turnaround
    
    def calculate_average_response_time(self) -> float:
        """Calculate average first response time."""
        response_times = [
            p.first_response_time for p in self.completed_queue 
            if p.first_response_time is not None
        ]
        
        if not response_times:
            return 0.0
        
        return round(sum(response_times) / len(response_times), 2)
    
    # ---- STATE SERIALIZATION FOR GUI ----
    def _get_return_dict(self) -> Dict[str, Any]:
        """Create the standardized return dictionary for GUI."""
        # Calculate averages
        avg_wait, avg_turn = self.calculate_statistics()
        avg_response = self.calculate_average_response_time()
        
        # Check if simulation is complete
        self._check_completion()
        
        return {
            # Time information
            'current_time': self.current_time,
            
            # Current execution status
            'current_pid': self.current_process.pid if self.current_process else None,
            
            # Queue information
            'ready_queue_pids': [p.pid for p in self.ready_queue],
            'ready_queue_size': len(self.ready_queue),
            
            # Process tables (for display)
            'processes_table': [p.to_dict() for p in self.processes],
            'completed_processes': [p.to_dict() for p in self.completed_queue],
            
            # Gantt chart data (deep copy to prevent external modification)
            'gantt_chart': [segment.copy() for segment in self.gantt_chart],
            
            # Statistics
            'avg_waiting': avg_wait,
            'avg_turnaround': avg_turn,
            'avg_response': avg_response,
            
            # State flags
            'is_finished': self.is_finished,
            
            # Additional information
            'algorithm_name': self.get_algorithm_name(),
            'total_processes': len(self.processes),
            'completed_count': len(self.completed_queue),
        }
        
        
    def get_process_by_pid(self, pid: str) -> Optional[Process]:
        """Get a process by its PID."""
        for process in self.processes:
            if process.pid == pid:
                return process
        return None