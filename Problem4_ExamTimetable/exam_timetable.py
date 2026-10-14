
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import math
import time


# ---------------- GRAPH COLORING ----------------

def build_graph(subjects, conflicts):
    graph = {subject: set() for subject in subjects}

    for first, second in conflicts:
        if first in graph and second in graph:
            graph[first].add(second)
            graph[second].add(first)

    return graph


def graph_coloring(subjects, conflicts):
    graph = build_graph(subjects, conflicts)

    # Try increasing numbers of slots to find the minimum.
    for limit in range(1, len(subjects) + 1):
        assigned = {}

        def solve():
            if len(assigned) == len(subjects):
                return True

            remaining = [
                s for s in subjects if s not in assigned
            ]

            # Choose the subject with the most conflicts first.
            subject = max(
                remaining,
                key=lambda s: sum(
                    1 for neighbor in graph[s]
                    if neighbor in assigned
                ) * 100 + len(graph[s])
            )

            forbidden = {
                assigned[n]
                for n in graph[subject]
                if n in assigned
            }

            for color in range(limit):
                if color not in forbidden:
                    assigned[subject] = color

                    if solve():
                        return True

                    del assigned[subject]

            return False

        if solve():
            return assigned.copy(), graph

    return None, graph


def validate_timetable(assignments, graph):
    for subject in graph:
        for neighbor in graph[subject]:
            if assignments[subject] == assignments[neighbor]:
                return False
    return True


# ---------------- MAIN APPLICATION ----------------

class ExamTimetableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Exam Timetable Scheduler")
        self.root.geometry("1150x750")
        self.root.minsize(900, 600)
        self.root.configure(bg="#F1F5FB")

        self.subjects = []
        self.conflicts = []
        self.assignments = {}
        self.graph = {}

        self.create_header()
        self.create_input_area()
        self.create_results_area()
        self.create_footer()

    # ---------------- HEADER ----------------

    def create_header(self):
        header = tk.Frame(self.root, bg="#17365D", height=95)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="EXAM TIMETABLE SCHEDULER",
            font=("Segoe UI", 21, "bold"),
            bg="#17365D",
            fg="white"
        ).pack(anchor="w", padx=25, pady=(18, 4))

        tk.Label(
            header,
            text="Graph Coloring | Automatic Conflict-Free Scheduling",
            font=("Segoe UI", 10),
            bg="#17365D",
            fg="#D9E8FF"
        ).pack(anchor="w", padx=27)

    # ---------------- INPUT AREA ----------------

    def create_input_area(self):
        panel = tk.Frame(
            self.root, bg="white",
            highlightbackground="#D9E2EF",
            highlightthickness=1
        )
        panel.pack(fill="x", padx=20, pady=15)

        tk.Label(
            panel,
            text="1. Add Your Subjects",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#17365D"
        ).grid(row=0, column=0, columnspan=3,
               sticky="w", padx=15, pady=(12, 7))

        self.subject_entry = ttk.Entry(panel, width=28)
        self.subject_entry.grid(
            row=1, column=0, padx=15, pady=5, sticky="ew"
        )
        self.subject_entry.bind(
            "<Return>", lambda event: self.add_subject()
        )

        ttk.Button(
            panel, text="Add Subject",
            command=self.add_subject
        ).grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(
            panel, text="Remove Selected",
            command=self.remove_subject
        ).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(
            panel,
            text="2. Select Two Subjects That Cannot Share An Exam Slot",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#17365D"
        ).grid(row=2, column=0, columnspan=3,
               sticky="w", padx=15, pady=(15, 7))

        self.first_box = ttk.Combobox(
            panel, state="readonly", width=25
        )
        self.first_box.grid(
            row=3, column=0, padx=15, pady=5, sticky="ew"
        )

        self.second_box = ttk.Combobox(
            panel, state="readonly", width=25
        )
        self.second_box.grid(
            row=3, column=1, padx=5, pady=5, sticky="ew"
        )

        ttk.Button(
            panel, text="Add Conflict",
            command=self.add_conflict
        ).grid(row=3, column=2, padx=5, pady=5)

        self.conflict_list = tk.Listbox(
            panel, height=3,
            font=("Segoe UI", 9),
            bg="#F8FAFC", fg="#24324A",
            selectbackground="#BBD5F5",
            relief="flat"
        )
        self.conflict_list.grid(
            row=4, column=0, columnspan=2,
            padx=15, pady=8, sticky="ew"
        )

        ttk.Button(
            panel, text="Remove Selected Conflict",
            command=self.remove_conflict
        ).grid(row=4, column=2, padx=5, pady=5)

        actions = tk.Frame(panel, bg="white")
        actions.grid(
            row=5, column=0, columnspan=3,
            sticky="w", padx=15, pady=(8, 15)
        )

        tk.Button(
            actions,
            text="Generate Timetable",
            command=self.generate_timetable,
            bg="#1D4ED8", fg="white",
            activebackground="#1E40AF",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=15, pady=8,
            cursor="hand2"
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            actions,
            text="Export CSV",
            command=self.export_csv,
            bg="#0F766E", fg="white",
            activebackground="#115E59",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=15, pady=8,
            cursor="hand2"
        ).pack(side="left", padx=8)

        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)

    # ---------------- RESULTS AREA ----------------

    def create_results_area(self):
        area = tk.Frame(self.root, bg="#F1F5FB")
        area.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        left = tk.Frame(
            area, bg="white",
            highlightbackground="#D9E2EF",
            highlightthickness=1
        )
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))

        right = tk.Frame(
            area, bg="white",
            highlightbackground="#D9E2EF",
            highlightthickness=1
        )
        right.pack(side="left", fill="both", expand=True, padx=(7, 0))

        tk.Label(
            left, text="Generated Timetable",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#17365D"
        ).pack(anchor="w", padx=12, pady=12)

        self.table = ttk.Treeview(
            left,
            columns=("subject", "slot"),
            show="headings"
        )
        self.table.heading("subject", text="Subject")
        self.table.heading("slot", text="Exam Time Slot")
        self.table.column("subject", width=200)
        self.table.column("slot", width=120, anchor="center")
        self.table.pack(
            fill="both", expand=True, padx=10, pady=(0, 10)
        )

        tk.Label(
            right, text="Conflict Graph",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#17365D"
        ).pack(anchor="w", padx=12, pady=(12, 4))

        tk.Label(
            right,
            text="Connected subjects must use different slots.",
            font=("Segoe UI", 9),
            bg="white", fg="#64748B"
        ).pack(anchor="w", padx=12)

        self.canvas = tk.Canvas(
            right, bg="#FAFCFF", highlightthickness=0
        )
        self.canvas.pack(
            fill="both", expand=True, padx=8, pady=8
        )
        self.canvas.bind("<Configure>", self.draw_graph)

    def create_footer(self):
        self.status = tk.Label(
            self.root,
            text="Add subjects and conflicts to begin.",
            anchor="w",
            bg="#E2EAF5", fg="#334155",
            font=("Segoe UI", 9), padx=15, pady=7
        )
        self.status.pack(fill="x", side="bottom")

    # ---------------- SUBJECT MANAGEMENT ----------------

    def add_subject(self):
        subject = self.subject_entry.get().strip()

        if not subject:
            messagebox.showwarning(
                "Missing Subject", "Enter a subject name first."
            )
            return

        if any(s.casefold() == subject.casefold()
               for s in self.subjects):
            messagebox.showwarning(
                "Duplicate Subject",
                "This subject has already been added."
            )
            return

        self.subjects.append(subject)
        self.subject_entry.delete(0, "end")
        self.refresh_dropdowns()
        self.clear_results()
        self.status.config(text=f"Added subject: {subject}")

    def remove_subject(self):
        selection = self.table.selection()

        if selection:
            subject = self.table.item(
                selection[0], "values"
            )[0]
        else:
            messagebox.showinfo(
                "Select Subject",
                "Select a subject in the timetable to remove it."
            )
            return

        if not messagebox.askyesno(
            "Remove Subject",
            f"Remove '{subject}' and its conflicts?"
        ):
            return

        self.subjects.remove(subject)
        self.conflicts = [
            pair for pair in self.conflicts
            if subject not in pair
        ]

        self.refresh_dropdowns()
        self.refresh_conflict_list()
        self.clear_results()
        self.status.config(text=f"Removed subject: {subject}")

    def refresh_dropdowns(self):
        self.first_box["values"] = self.subjects
        self.second_box["values"] = self.subjects

        self.first_box.set("")
        self.second_box.set("")

    # ---------------- CONFLICT MANAGEMENT ----------------

    def add_conflict(self):
        first = self.first_box.get()
        second = self.second_box.get()

        if not first or not second:
            messagebox.showwarning(
                "Select Subjects",
                "Choose both subjects before adding a conflict."
            )
            return

        if first == second:
            messagebox.showwarning(
                "Invalid Conflict",
                "Choose two different subjects."
            )
            return

        pair = (first, second)
        reverse_pair = (second, first)

        if pair in self.conflicts or reverse_pair in self.conflicts:
            messagebox.showinfo(
                "Already Exists",
                "This conflict has already been added."
            )
            return

        self.conflicts.append(pair)
        self.refresh_conflict_list()
        self.clear_results()
        self.status.config(
            text=f"Conflict added: {first} and {second}"
        )

    def refresh_conflict_list(self):
        self.conflict_list.delete(0, "end")

        for first, second in self.conflicts:
            self.conflict_list.insert(
                "end", f"{first}  <->  {second}"
            )

    def remove_conflict(self):
        selection = self.conflict_list.curselection()

        if not selection:
            messagebox.showinfo(
                "Select Conflict",
                "Select a conflict from the list first."
            )
            return

        index = selection[0]
        removed = self.conflicts.pop(index)
        self.refresh_conflict_list()
        self.clear_results()
        self.status.config(
            text=f"Removed conflict: {removed[0]} and {removed[1]}"
        )

    # ---------------- TIMETABLE GENERATION ----------------

    def clear_results(self):
        self.assignments = {}
        self.graph = {}

        for item in self.table.get_children():
            self.table.delete(item)

        self.canvas.delete("all")

    def generate_timetable(self):
        if not self.subjects:
            messagebox.showwarning(
                "No Subjects",
                "Add at least one subject before generating."
            )
            return

        start = time.perf_counter()
        assignments, graph = graph_coloring(
            self.subjects, self.conflicts
        )
        elapsed = (time.perf_counter() - start) * 1000

        if assignments is None:
            messagebox.showerror(
                "Scheduling Failed",
                "No valid timetable was found."
            )
            return

        self.assignments = assignments
        self.graph = graph

        if not validate_timetable(assignments, graph):
            messagebox.showerror(
                "Validation Failed",
                "A scheduling conflict was detected."
            )
            return

        for item in self.table.get_children():
            self.table.delete(item)

        for subject in self.subjects:
            slot = assignments[subject] + 1
            self.table.insert(
                "", "end", values=(subject, f"Slot {slot}")
            )

        slot_count = len(set(assignments.values()))

        self.status.config(
            text=(
                f"Timetable generated successfully | "
                f"{len(self.subjects)} subjects | "
                f"{slot_count} time slot(s) | "
                f"0 conflicts | {elapsed:.3f} ms"
            )
        )

        self.draw_graph()

    # ---------------- GRAPH DRAWING ----------------

    def draw_graph(self, event=None):
        if not hasattr(self, "canvas"):
            return

        self.canvas.delete("all")

        if not self.subjects or not self.assignments:
            self.canvas.create_text(
                max(self.canvas.winfo_width() // 2, 100),
                max(self.canvas.winfo_height() // 2, 100),
                text="Generate a timetable to view the graph",
                fill="#64748B",
                font=("Segoe UI", 10)
            )
            return

        width = max(self.canvas.winfo_width(), 300)
        height = max(self.canvas.winfo_height(), 250)

        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) * 0.34
        positions = {}

        count = len(self.subjects)

        for i, subject in enumerate(self.subjects):
            angle = (2 * math.pi * i / count) - math.pi / 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[subject] = (x, y)

        # Draw conflict edges
        for subject in self.subjects:
            for neighbor in self.graph.get(subject, set()):
                if self.subjects.index(subject) < self.subjects.index(neighbor):
                    x1, y1 = positions[subject]
                    x2, y2 = positions[neighbor]
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill="#AABBD0", width=1.5
                    )

        palette = [
            "#2563EB", "#059669", "#D97706",
            "#7C3AED", "#DB2777", "#0891B2",
            "#65A30D", "#DC2626"
        ]

        for subject in self.subjects:
            x, y = positions[subject]
            color = palette[
                self.assignments[subject] % len(palette)
            ]

            self.canvas.create_oval(
                x - 30, y - 22, x + 30, y + 22,
                fill=color, outline="white", width=2
            )

            label = subject
            if len(label) > 11:
                label = label[:10] + "..."

            self.canvas.create_text(
                x, y,
                text=label,
                fill="white",
                font=("Segoe UI", 8, "bold")
            )

    # ---------------- EXPORT CSV ----------------

    def export_csv(self):
        if not self.assignments:
            messagebox.showwarning(
                "No Timetable",
                "Generate a timetable before exporting."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Save Exam Timetable",
            defaultextension=".csv",
            initialfile="exam_timetable.csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not path:
            return

        try:
            with open(
                path, "w", newline="", encoding="utf-8"
            ) as file:
                writer = csv.writer(file)
                writer.writerow(["Subject", "Time Slot"])

                for subject in self.subjects:
                    writer.writerow([
                        subject,
                        f"Slot {self.assignments[subject] + 1}"
                    ])

            messagebox.showinfo(
                "Export Complete",
                f"Timetable saved successfully:\n{path}"
            )

        except OSError as error:
            messagebox.showerror(
                "Export Error", str(error)
            )


# ---------------- START PROGRAM ----------------

if __name__ == "__main__":
    root = tk.Tk()
    app = ExamTimetableApp(root)
    root.mainloop()
