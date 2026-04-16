import tkinter as tk
from tkinter import messagebox, ttk

# process model
from src.core.models import Process

# schedulers
from src.core.algorithms.fcfs.fcfs_scheduler import FCFSScheduler
from src.core.algorithms.sjf.sjf_scheduler import SJFScheduler
from src.core.algorithms.priority.priority_scheduler import PriorityScheduler
from src.core.algorithms.round_robin.rr_scheduler import RoundRobinScheduler

# ui options
ALGO_FCFS = "FCFS"
ALGO_SJF = "SJF"
ALGO_PRIORITY = "Priority"
ALGO_RR = "Round Robin"


# globals
scheduler = None
initial_processes = []  # process queue
running = False
tick_job = None
pid_to_color = {}
color_index = 0

# gantt chart settings
SLOT_WIDTH = 40
SLOT_HEIGHT = 40
CHART_MARGIN_X = 20
CHART_MARGIN_Y = 25
COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]


# main window
root = tk.Tk()
root.title("CPU Scheduling Simulator")
root.geometry("1250x760")
root.minsize(1050, 680)

root.columnconfigure(0, weight=1)
root.rowconfigure(2, weight=1)

# tkinter stuffs
algorithm_var = tk.StringVar(value=ALGO_FCFS)
preemptive_var = tk.BooleanVar(value=False)
quantum_var = tk.StringVar(value="2")
live_var = tk.BooleanVar(value=True)

pid_var = tk.StringVar()
arrival_var = tk.StringVar(value="")
burst_var = tk.StringVar()
priority_var = tk.StringVar(value="0")

process_count_var = tk.StringVar(value="Processes: 0")
status_var = tk.StringVar(value="Idle")
time_var = tk.StringVar(value="Current Time: 0")
avg_wait_var = tk.StringVar(value="Average Waiting Time: 0.00")
avg_turn_var = tk.StringVar(value="Average Turnaround Time: 0.00")


# for input fields depending on algo
def set_algorithm_fields(event=None):
    algo = algorithm_var.get()

    if algo in (ALGO_SJF, ALGO_PRIORITY):
        preemptive_check.state(["!disabled"])
    else:
        preemptive_var.set(False)
        preemptive_check.state(["disabled"])

    if algo == ALGO_RR:
        quantum_label.grid()
        quantum_entry.grid()
    else:
        quantum_label.grid_remove()
        quantum_entry.grid_remove()

    if algo == ALGO_PRIORITY:
        priority_label.grid()
        priority_entry.grid()
    else:
        priority_label.grid_remove()
        priority_entry.grid_remove()


# table and metrics and gantt update
def update_ui():
    for row in process_table.get_children():
        process_table.delete(row)

    # if running show processes from the scheduler, if not we show initial processes
    processes_to_display = scheduler.processes if scheduler else initial_processes
    current_time = scheduler.current_time if scheduler else 0
 
    # sort by arrival time
    for p in sorted(processes_to_display, key=lambda x: x.arrival_time):
        if p.is_completed or p.remaining_time == 0:
            status = "Done"
        elif p.arrival_time > current_time:
            status = "Future"
        elif scheduler and scheduler.current_process and scheduler.current_process.pid == p.pid and running:
            status = "Running"
        else:
            status = "Ready"

        priority_display = p.priority if p.priority is not None else "-"

        process_table.insert("", "end", values=(
            p.pid, p.arrival_time, p.burst_time, priority_display, p.remaining_time, status
        ))

    process_count_var.set(f"Processes: {len(processes_to_display)}")

    # making sure we don't use null reference
    if not scheduler:
        return

    # for metrics display
    time_var.set(f"Current Time: {scheduler.current_time}")
    avg_wait, avg_turn = scheduler.calculate_statistics()
    avg_wait_var.set(f"Average Waiting Time: {avg_wait:.2f}")
    avg_turn_var.set(f"Average Turnaround Time: {avg_turn:.2f}")

    # reset the chart everytime and redraw
    chart_canvas.delete("all")
    
    # gantt is like a timeline of processes
    timeline = []
    current_time = 0
    for segment in scheduler.gantt_chart:
        # Pad idle gaps
        if segment['start'] > current_time:
            timeline.extend(["IDLE"] * (segment['start'] - current_time))
            
        timeline.extend([segment['pid']] * (segment['end'] - segment['start']))
        current_time = segment['end']

    # idle time when all processes are done
    if scheduler.current_time > current_time:
        timeline.extend(["IDLE"] * (scheduler.current_time - current_time))

    if not timeline: return

    width = chart_canvas.winfo_width()
    if width < 50: width = 500
    slots_per_row = max(1, (width - 2 * CHART_MARGIN_X) // SLOT_WIDTH)

    # gantt chart blocks
    for i, pid in enumerate(timeline):
        row = i // slots_per_row
        col = i % slots_per_row
        x1 = CHART_MARGIN_X + col * SLOT_WIDTH
        y1 = CHART_MARGIN_Y + row * (SLOT_HEIGHT + 24)
        x2 = x1 + SLOT_WIDTH
        y2 = y1 + SLOT_HEIGHT

        color = "#eceff1" if pid == "IDLE" else pid_to_color.get(pid, "#90caf9")
       
        chart_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#37474f")
        chart_canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=pid, font=("Segoe UI", 9, "bold"))
        chart_canvas.create_text(x1, y2 + 10, text=str(i), anchor="w", font=("Segoe UI", 8))

        # end time on last block
        if i == len(timeline) - 1:
            chart_canvas.create_text(x2, y2 + 10, text=str(i + 1), anchor="e", font=("Segoe UI", 8))
    
    bbox = chart_canvas.bbox("all")
    if bbox:
        chart_canvas.configure(scrollregion=(0, 0, bbox[2], bbox[3] + 20))


def add_process():
    global initial_processes, color_index

    pid = pid_var.get().strip()
    if not pid:
        messagebox.showerror("Error", "PID is required.")
        return

    # we mustn't allow duplicate PIDs 
    existing = scheduler.processes if scheduler else initial_processes
    if any(p.pid == pid for p in existing):
        messagebox.showerror("Error", f"Process ID '{pid}' already exists.")
        return

    # we get input and validate it
    try:
        burst = int(burst_var.get())
        if burst <= 0: raise ValueError
        arrival_str = arrival_var.get().strip()
        
        current_time = scheduler.current_time if scheduler else 0
        arrival = int(arrival_str) if arrival_str else current_time
        
        if live_var.get() and arrival < current_time:
            arrival = current_time

        # only use priority if user selected priority scheduler
        priority = int(priority_var.get()) if algorithm_var.get() == ALGO_PRIORITY else None
        
    except ValueError:
        messagebox.showerror("Error", "Arrival and Priority must be integers. Burst must be > 0.")
        return

    # creating the object with a try in case it errors
    try:
        new_process = Process(pid=pid, arrival_time=arrival, burst_time=burst, priority=priority)
    except ValueError as e:
        messagebox.showerror("Error", str(e))
        return

    # add process dynamically if running, but if not we add to initial
    if scheduler:
        scheduler.add_dynamic_process(new_process)
    else:
        initial_processes.append(new_process)

    # for color
    if pid not in pid_to_color:
        pid_to_color[pid] = COLORS[color_index % len(COLORS)]
        color_index += 1

    # again we reset and update just like gantt
    pid_var.set("")
    burst_var.set("")
    arrival_var.set("") 
    priority_var.set("") 
    status_var.set(f"Process {pid} added")
    
    update_ui()


def finish_simulation():
    pause_button.config(state="disabled", text="Pause")
    start_button.config(state="normal")
    algorithm_combo.config(state="readonly")
    set_algorithm_fields()
    status_var.set("Finished")


# 1 unit loop for live mode
def tick():
    global tick_job, running
    tick_job = None
    
    if not running or not scheduler: return

    state = scheduler.tick()
    update_ui()

    if state.get('is_finished', False):
        status_var.set("Idle (waiting for new process)")

    tick_job = root.after(1000, tick)


def start_simulation():
    global running, tick_job, scheduler
    if running: return

    if not initial_processes and not scheduler:
        messagebox.showwarning("Warning", "Add at least one process first.")
        return

    # we must initialize the scheduler
    if not scheduler:
        algo = algorithm_var.get()
        preemptive = preemptive_var.get()

        try:
            if algo == ALGO_FCFS:
                scheduler = FCFSScheduler(initial_processes)
            elif algo == ALGO_SJF:
                scheduler = SJFScheduler(initial_processes, preemptive=preemptive)
            elif algo == ALGO_PRIORITY:
                scheduler = PriorityScheduler(initial_processes, preemptive=preemptive)
            elif algo == ALGO_RR:
                quantum = int(quantum_var.get())
                if quantum <= 0: raise ValueError
                scheduler = RoundRobinScheduler(initial_processes, quantum=quantum)
        except ValueError:
             messagebox.showerror("Error", "Quantum must be a positive integer.")
             return
        
        if not scheduler:
            messagebox.showerror("Error", f"Scheduler {algo} failed to initialize!")
            return

    # prevent ui settings from changing while running
    running = True
    pause_button.config(state="normal", text="Pause")
    start_button.config(state="disabled")
    algorithm_combo.config(state="disabled")
    preemptive_check.state(["disabled"])
    quantum_entry.config(state="disabled")

    if live_var.get():
        status_var.set("Running live scheduler")
        tick_job = root.after(1000, tick)
    else:
        status_var.set("Running non-live mode")
        
        # skip timing if not live mode
        while not scheduler.is_finished:
            scheduler.tick()
            
        running = False
        update_ui()
        finish_simulation()


def toggle_pause():
    global running, tick_job
    if not live_var.get() or not scheduler: return

    if not running:
        running = True
        pause_button.config(text="Pause")
        status_var.set("Resumed")
        tick_job = root.after(1000, tick)
    else:
        running = False
        if tick_job:
            root.after_cancel(tick_job)
            tick_job = None
        pause_button.config(text="Resume")
        status_var.set("Paused")


def reset_simulation():
    global scheduler, running, tick_job, color_index, initial_processes
    
    if tick_job:
        root.after_cancel(tick_job)
        tick_job = None

    scheduler = None
    initial_processes.clear()
    running = False
    pid_to_color.clear()
    color_index = 0

    # reset ui
    start_button.config(state="normal")
    pause_button.config(state="disabled", text="Pause")
    quantum_entry.config(state="normal")
    algorithm_combo.config(state="readonly")
    set_algorithm_fields()

    time_var.set("Current Time: 0")
    avg_wait_var.set("Average Waiting Time: 0.00")
    avg_turn_var.set("Average Turnaround Time: 0.00")
    status_var.set("Idle")
    process_count_var.set("Processes: 0")

    for row in process_table.get_children():
        process_table.delete(row)
        
    chart_canvas.delete("all")
    chart_canvas.configure(scrollregion=(0, 0, 0, 0))


# ui layout

# config stuffs
config_frame = ttk.LabelFrame(root, text="Scheduler Configuration", padding=10)
config_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
config_frame.columnconfigure(10, weight=1)

ttk.Label(config_frame, text="Algorithm:").grid(row=0, column=0, sticky="w")
algorithm_combo = ttk.Combobox(
    config_frame, textvariable=algorithm_var,
    values=[ALGO_FCFS, ALGO_SJF, ALGO_PRIORITY, ALGO_RR],
    state="readonly", width=16
)
algorithm_combo.grid(row=0, column=1, padx=(6, 16), sticky="w")
algorithm_combo.bind("<<ComboboxSelected>>", set_algorithm_fields)

preemptive_check = ttk.Checkbutton(config_frame, text="Preemptive", variable=preemptive_var)
preemptive_check.grid(row=0, column=2, sticky="w", padx=(0, 16))

quantum_label = ttk.Label(config_frame, text="Quantum:")
quantum_label.grid(row=0, column=3, sticky="w")
quantum_entry = ttk.Entry(config_frame, textvariable=quantum_var, width=7)
quantum_entry.grid(row=0, column=4, padx=(6, 16), sticky="w")

live_check = ttk.Checkbutton(config_frame, text="Live scheduling (1 sec = 1 time unit)", variable=live_var)
live_check.grid(row=0, column=5, sticky="w")

start_button = ttk.Button(config_frame, text="Start", command=start_simulation)
start_button.grid(row=0, column=6, padx=(20, 6))

pause_button = ttk.Button(config_frame, text="Pause", command=toggle_pause, state="disabled")
pause_button.grid(row=0, column=7, padx=6)

reset_button = ttk.Button(config_frame, text="Reset", command=reset_simulation)
reset_button.grid(row=0, column=8, padx=6)

# for process
process_frame = ttk.LabelFrame(root, text="Add Process", padding=10)
process_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
process_frame.columnconfigure(12, weight=1)

ttk.Label(process_frame, text="PID:").grid(row=0, column=0, sticky="w")
ttk.Entry(process_frame, textvariable=pid_var, width=10).grid(row=0, column=1, padx=(6, 12), sticky="w")

ttk.Label(process_frame, text="Arrival:").grid(row=0, column=2, sticky="w")
ttk.Entry(process_frame, textvariable=arrival_var, width=8).grid(row=0, column=3, padx=(6, 12), sticky="w")

ttk.Label(process_frame, text="Burst:").grid(row=0, column=4, sticky="w")
ttk.Entry(process_frame, textvariable=burst_var, width=8).grid(row=0, column=5, padx=(6, 12), sticky="w")

priority_label = ttk.Label(process_frame, text="Priority:")
priority_label.grid(row=0, column=6, sticky="w")
priority_entry = ttk.Entry(process_frame, textvariable=priority_var, width=8)
priority_entry.grid(row=0, column=7, padx=(6, 12), sticky="w")

ttk.Button(process_frame, text="Add Process", command=add_process).grid(row=0, column=8, padx=(6, 10))
ttk.Label(process_frame, textvariable=process_count_var).grid(row=0, column=9, padx=(8, 0), sticky="w")
ttk.Label(process_frame, textvariable=status_var, foreground="#0b5a8f").grid(row=0, column=10, padx=(20, 0), sticky="w")

# main display
main_frame = ttk.Frame(root)
main_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
main_frame.columnconfigure(0, weight=3)
main_frame.columnconfigure(1, weight=2)
main_frame.rowconfigure(0, weight=1)

# gantt
chart_frame = ttk.LabelFrame(main_frame, text="Live Gantt Chart", padding=8)
chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
chart_frame.rowconfigure(0, weight=1)
chart_frame.columnconfigure(0, weight=1)

chart_canvas = tk.Canvas(chart_frame, bg="white", highlightthickness=1, highlightbackground="#cfd8dc")
chart_canvas.grid(row=0, column=0, sticky="nsew")
chart_scroll = ttk.Scrollbar(chart_frame, orient="vertical", command=chart_canvas.yview)
chart_canvas.configure(yscrollcommand=chart_scroll.set)
chart_scroll.grid(row=0, column=1, sticky="ns")

# table and metrics right below
right_frame = ttk.Frame(main_frame)
right_frame.grid(row=0, column=1, sticky="nsew")
right_frame.rowconfigure(0, weight=1)
right_frame.rowconfigure(1, weight=0)
right_frame.columnconfigure(0, weight=1)

table_frame = ttk.LabelFrame(right_frame, text="Remaining Burst Time Table", padding=8)
table_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
table_frame.rowconfigure(0, weight=1)
table_frame.columnconfigure(0, weight=1)

process_table = ttk.Treeview(
    table_frame,
    columns=("pid", "arrival", "burst", "priority", "remaining", "status"),
    show="headings", height=14
)

cols = [("pid", "PID", 80), ("arrival", "Arrival", 70), ("burst", "Burst", 65),
        ("priority", "Priority", 70), ("remaining", "Remaining", 80), ("status", "Status", 90)]
for col, text, width in cols:
    process_table.heading(col, text=text)
    process_table.column(col, width=width, anchor="center")

table_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=process_table.yview)
process_table.configure(yscrollcommand=table_scroll.set)
process_table.grid(row=0, column=0, sticky="nsew")
table_scroll.grid(row=0, column=1, sticky="ns")

metrics_frame = ttk.LabelFrame(right_frame, text="Metrics", padding=10)
metrics_frame.grid(row=1, column=0, sticky="ew")

ttk.Label(metrics_frame, textvariable=time_var).grid(row=0, column=0, sticky="w", pady=2)
ttk.Label(metrics_frame, textvariable=avg_wait_var).grid(row=1, column=0, sticky="w", pady=2)
ttk.Label(metrics_frame, textvariable=avg_turn_var).grid(row=2, column=0, sticky="w", pady=2)


def main():
    set_algorithm_fields() 
    root.mainloop()

if __name__ == "__main__":
    main()