import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import time
import sqlite3
from datetime import datetime
import csv

# DB Setup
conn = sqlite3.connect("task_timer.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT,
    start_time TEXT,
    end_time TEXT,
    duration REAL
)
""")
conn.commit()

class TaskTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Productivity Timer")
        self.root.geometry("500x500")

        self.task_name_var = tk.StringVar()
        self.running = False
        self.elapsed_time = 0
        self.start_time = None

        # Header
        tk.Label(root, text="🕒 Task-based Time Tracker", font=("Arial", 16, "bold")).pack(pady=10)

        # Task Entry
        entry_frame = tk.Frame(root)
        entry_frame.pack(pady=10)

        tk.Label(entry_frame, text="Task Name:").pack(side=tk.LEFT)
        tk.Entry(entry_frame, textvariable=self.task_name_var, width=30).pack(side=tk.LEFT, padx=5)

        # Timer Label
        self.timer_label = tk.Label(root, text="Timer: 00:00:00", font=("Courier", 16))
        self.timer_label.pack(pady=10)

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(btn_frame, text="Start", width=10, bg="green", fg="white", command=self.start_timer)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = tk.Button(btn_frame, text="Stop", width=10, bg="red", fg="white", command=self.stop_timer, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)

        self.report_btn = tk.Button(root, text="📊 View Report", command=self.view_report)
        self.report_btn.pack(pady=5)

    def update_timer(self):
        if self.running:
            self.elapsed_time = time.time() - self.start_time
            mins, secs = divmod(int(self.elapsed_time), 60)
            hours, mins = divmod(mins, 60)
            self.timer_label.config(text=f"Timer: {hours:02}:{mins:02}:{secs:02}")
            self.root.after(1000, self.update_timer)

    def start_timer(self):
        task = self.task_name_var.get().strip()
        if not task:
            messagebox.showwarning("Warning", "Please enter a task name.")
            return
        self.running = True
        self.start_time = time.time()
        self.start_datetime = datetime.now()
        self.update_timer()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_timer(self):
        if not self.running:
            return
        self.running = False
        end_datetime = datetime.now()
        duration = round(time.time() - self.start_time, 2)

        cursor.execute("INSERT INTO tasks (task_name, start_time, end_time, duration) VALUES (?, ?, ?, ?)", (
            self.task_name_var.get(),
            self.start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            end_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            duration
        ))
        conn.commit()

        mins = round(duration / 60, 2)
        messagebox.showinfo("Saved", f"Task saved! Time spent: {mins} minutes.")

        self.task_name_var.set("")
        self.timer_label.config(text="Timer: 00:00:00")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def view_report(self):
        report_window = tk.Toplevel(self.root)
        report_window.title("Task Report")
        report_window.geometry("600x400")

        tk.Label(report_window, text="📋 Task Time Report", font=("Arial", 14, "bold")).pack(pady=10)

        # Treeview Table
        columns = ("Task", "Start", "End", "Duration")
        tree = ttk.Treeview(report_window, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")

        cursor.execute("SELECT task_name, start_time, end_time, duration FROM tasks ORDER BY id DESC")
        for row in cursor.fetchall():
            mins = round(row[3] / 60, 2)
            tree.insert("", tk.END, values=(row[0], row[1], row[2], f"{mins} mins"))

        tree.pack(pady=10, fill=tk.BOTH, expand=True)

        # Export button
        export_btn = tk.Button(report_window, text="⬇️ Export to CSV", command=self.export_csv)
        export_btn.pack(pady=5)

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        cursor.execute("SELECT task_name, start_time, end_time, duration FROM tasks")
        rows = cursor.fetchall()

        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Task", "Start Time", "End Time", "Duration (seconds)"])
            writer.writerows(rows)

        messagebox.showinfo("Exported", "CSV file exported successfully!")

# Run
if __name__ == "__main__":
    root = tk.Tk()
    app = TaskTimerApp(root)
    root.mainloop()
