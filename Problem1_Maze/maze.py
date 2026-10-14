
import csv
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from collections import deque


# =========================================================
# 1. MAZE GENERATION
# =========================================================

KEYS = "abcdef"
CELL_COLORS = {
    "#": "#263746",
    ".": "#FFFFFF",
    "S": "#43A879",
    "E": "#E65B65",
    "a": "#5AA9F5",
    "b": "#35B7AA",
    "c": "#B18AE0",
    "d": "#E7A34A",
    "e": "#D9C84D",
    "f": "#E887B7",
    "A": "#A9D6FF",
    "B": "#A3E6DF",
    "C": "#D9C8F5",
    "D": "#F7D6A7",
    "E": "#E65B65",
    "F": "#F4C4DC",
}


def key_bit(letter):
    return 1 << (ord(letter.lower()) - ord("a"))


def inventory_text(mask):
    collected = [k for k in KEYS if mask & key_bit(k)]
    return ", ".join(collected) if collected else "None"


def generate_maze(size):
    """Generate a random perfect maze using recursive backtracking."""

    grid = [["#" for _ in range(size)] for _ in range(size)]
    start = (1, 1)
    end = (size - 2, size - 2)

    grid[start[0]][start[1]] = "."

    stack = [start]
    visited = {start}

    directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]

    while stack:
        r, c = stack[-1]
        options = []

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if (
                1 <= nr < size - 1
                and 1 <= nc < size - 1
                and (nr, nc) not in visited
            ):
                options.append((nr, nc, dr, dc))

        if options:
            nr, nc, dr, dc = random.choice(options)

            grid[r + dr // 2][c + dc // 2] = "."
            grid[nr][nc] = "."
            visited.add((nr, nc))
            stack.append((nr, nc))
        else:
            stack.pop()

    grid[start[0]][start[1]] = "S"
    grid[end[0]][end[1]] = "E"

    # Find the unique route through the maze before adding doors.
    route = basic_path(grid, start, end)

    # Larger mazes can contain more key/door pairs.
    desired_pairs = min(6, max(1, (size - 7) // 2))
    possible_pairs = max(1, (len(route) - 2) // 2)
    pair_count = min(desired_pairs, possible_pairs)

    # Place keys first, then their corresponding doors.
    route_length = len(route) - 1
    key_positions = []
    door_positions = []

    for i in range(pair_count):
        index = ((i + 1) * route_length) // (2 * pair_count + 1)
        key_positions.append(index)

    for i in range(pair_count):
        index = ((pair_count + i + 1) * route_length) // (
            2 * pair_count + 1
        )
        door_positions.append(index)

    # Avoid placing multiple items in the same cell.
    used_positions = set()

    for i in range(pair_count):
        key_pos = route[key_positions[i]]
        door_pos = route[door_positions[i]]

        if (
            key_pos in used_positions
            or door_pos in used_positions
            or key_pos in (start, end)
            or door_pos in (start, end)
        ):
            continue

        key_letter = KEYS[i]
        kr, kc = key_pos
        dr, dc = door_pos

        grid[kr][kc] = key_letter
        grid[dr][dc] = key_letter.upper()

        used_positions.add(key_pos)
        used_positions.add(door_pos)

    return grid


def basic_path(grid, start, end):
    """Find a route in the maze before keys and doors are added."""

    rows, cols = len(grid), len(grid[0])
    queue = deque([start])
    parent = {start: None}

    while queue:
        r, c = queue.popleft()

        if (r, c) == end:
            break

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc

            if (
                0 <= nr < rows
                and 0 <= nc < cols
                and grid[nr][nc] != "#"
                and (nr, nc) not in parent
            ):
                parent[(nr, nc)] = (r, c)
                queue.append((nr, nc))

    path = []
    current = end

    while current is not None:
        path.append(current)
        current = parent[current]

    return path[::-1]


# =========================================================
# 2. BFS SOLVER
# =========================================================

def solve_bfs(grid):
    rows, cols = len(grid), len(grid[0])
    start = None

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "S":
                start = (r, c)
                break
        if start:
            break

    if start is None:
        return None

    # A state includes position and the keys collected.
    start_state = (start[0], start[1], 0)

    queue = deque([(start_state, 0)])
    visited = {start_state}
    parent = {start_state: None}

    search_frames = []
    end_state = None

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        state, distance = queue.popleft()
        r, c, keys = state

        search_frames.append((state, distance))

        if grid[r][c] == "E":
            end_state = state
            break

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if not (0 <= nr < rows and 0 <= nc < cols):
                continue

            cell = grid[nr][nc]

            if cell == "#":
                continue

            # A door can only be crossed with its matching key.
            if "A" <= cell <= "F":
                required_key = key_bit(cell)

                if not (keys & required_key):
                    continue

            # Collect a key upon entering its cell.
            new_keys = keys

            if "a" <= cell <= "f":
                new_keys |= key_bit(cell)

            new_state = (nr, nc, new_keys)

            if new_state not in visited:
                visited.add(new_state)
                parent[new_state] = state
                queue.append((new_state, distance + 1))

    if end_state is None:
        return {
            "frames": search_frames,
            "path": [],
            "distance": -1,
            "keys": 0,
            "visited_count": len(visited),
        }

    # Reconstruct the shortest path.
    state_path = []
    current = end_state

    while current is not None:
        state_path.append(current)
        current = parent[current]

    state_path.reverse()

    path = [(state[0], state[1]) for state in state_path]

    return {
        "frames": search_frames,
        "path": path,
        "distance": len(path) - 1,
        "keys": end_state[2],
        "visited_count": len(visited),
    }


# =========================================================
# 3. INTERACTIVE APPLICATION
# =========================================================

class MazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Maze Explorer | BFS Pathfinding")
        self.root.geometry("1100x850")
        self.root.minsize(850, 650)
        self.root.configure(bg="#EAF3FB")

        self.maze = []
        self.rows = 15
        self.cols = 15

        self.result = None
        self.frame_index = 0
        self.path_index = 0
        self.visited_positions = set()
        self.visible_path = []
        self.current_position = None

        self.running = False
        self.paused = False
        self.after_id = None
        self.phase = "idle"

        self.build_ui()
        self.change_maze()

    # -----------------------------------------------------
    # USER INTERFACE
    # -----------------------------------------------------

    def build_ui(self):
        header = tk.Frame(self.root, bg="#D6E9FA", pady=12)
        header.pack(fill="x")

        tk.Label(
            header,
            text="MAZE EXPLORER",
            font=("Segoe UI", 22, "bold"),
            fg="#163B63",
            bg="#D6E9FA",
        ).pack()

        tk.Label(
            header,
            text="Explore • Collect keys • Unlock doors • Find the shortest path",
            font=("Segoe UI", 10),
            fg="#436783",
            bg="#D6E9FA",
        ).pack(pady=(3, 0))

        controls = tk.Frame(self.root, bg="#EAF3FB", pady=10)
        controls.pack(fill="x", padx=14)

        tk.Label(
            controls,
            text="Maze size:",
            font=("Segoe UI", 10, "bold"),
            bg="#EAF3FB",
            fg="#24445F",
        ).pack(side="left", padx=(0, 5))

        self.size_var = tk.StringVar(value="15 x 15")

        size_box = ttk.Combobox(
            controls,
            textvariable=self.size_var,
            values=["9 x 9", "11 x 11", "13 x 13", "15 x 15",
                    "17 x 17", "19 x 19", "21 x 21"],
            state="readonly",
            width=9,
        )
        size_box.pack(side="left", padx=(0, 12))

        self.make_button(controls, "Change Maze", self.change_maze).pack(
            side="left", padx=4
        )
        self.make_button(controls, "Solve Maze", self.start_solve,
                         "#2878B5").pack(side="left", padx=4)
        self.make_button(controls, "Pause", self.toggle_pause).pack(
            side="left", padx=4
        )
        self.make_button(controls, "Reset", self.reset_maze).pack(
            side="left", padx=4
        )
        self.make_button(controls, "Export CSV", self.export_csv).pack(
            side="left", padx=4
        )

        speed_frame = tk.Frame(self.root, bg="#EAF3FB")
        speed_frame.pack(fill="x", padx=18, pady=(0, 8))

        tk.Label(
            speed_frame,
            text="Animation speed",
            bg="#EAF3FB",
            fg="#24445F",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")

        self.speed_var = tk.IntVar(value=100)

        tk.Scale(
            speed_frame,
            from_=20,
            to=400,
            orient="horizontal",
            variable=self.speed_var,
            bg="#EAF3FB",
            fg="#24445F",
            highlightthickness=0,
            length=200,
            showvalue=True,
            label="Delay (milliseconds)",
        ).pack(side="left", padx=10)

        main = tk.Frame(self.root, bg="#EAF3FB")
        main.pack(fill="both", expand=True, padx=14, pady=4)

        self.canvas = tk.Canvas(
            main,
            bg="white",
            highlightthickness=1,
            highlightbackground="#C6D9E8",
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        side = tk.Frame(main, bg="#F8FBFE", width=230, padx=14, pady=14)
        side.pack(side="right", fill="y", padx=(12, 0))
        side.pack_propagate(False)

        tk.Label(
            side,
            text="RESULTS",
            font=("Segoe UI", 14, "bold"),
            bg="#F8FBFE",
            fg="#163B63",
        ).pack(anchor="w", pady=(0, 12))

        self.distance_label = self.make_stat(side, "Shortest distance", "—")
        self.explored_label = self.make_stat(side, "Explored states", "0")
        self.keys_label = self.make_stat(side, "Keys at exit", "None")
        self.status_label = self.make_stat(side, "Status", "Ready")

        tk.Label(
            side,
            text="LEGEND",
            font=("Segoe UI", 12, "bold"),
            bg="#F8FBFE",
            fg="#163B63",
        ).pack(anchor="w", pady=(18, 8))

        legend = [
            ("Start", "#43A879"),
            ("Exit", "#E65B65"),
            ("Wall", "#263746"),
            ("Explored", "#FFE08A"),
            ("Shortest path", "#FF8A32"),
            ("Key", "#5AA9F5"),
            ("Door", "#A9D6FF"),
        ]

        for label, color in legend:
            row = tk.Frame(side, bg="#F8FBFE")
            row.pack(fill="x", pady=3)

            tk.Label(
                row, text="  ", bg=color, width=3, relief="solid",
                bd=1
            ).pack(side="left", padx=(0, 8))

            tk.Label(
                row, text=label, bg="#F8FBFE",
                fg="#24445F", font=("Segoe UI", 9)
            ).pack(side="left")

        self.message_label = tk.Label(
            self.root,
            text="Click Change Maze to generate a new puzzle.",
            bg="#D6E9FA",
            fg="#24445F",
            font=("Segoe UI", 10),
            pady=8,
        )
        self.message_label.pack(fill="x", side="bottom")

        self.canvas.bind("<Configure>", lambda event: self.draw_maze())

    def make_button(self, parent, text, command, color="#4D91C7"):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            activebackground="#1F5F91",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=7,
        )

    def make_stat(self, parent, title, value):
        box = tk.Frame(parent, bg="#EAF3FB", padx=9, pady=8)
        box.pack(fill="x", pady=4)

        tk.Label(
            box, text=title, bg="#EAF3FB",
            fg="#436783", font=("Segoe UI", 9)
        ).pack(anchor="w")

        value_label = tk.Label(
            box, text=value, bg="#EAF3FB",
            fg="#163B63", font=("Segoe UI", 12, "bold"),
            wraplength=185, justify="left"
        )
        value_label.pack(anchor="w")

        return value_label

    # -----------------------------------------------------
    # CHANGE / RESET MAZE
    # -----------------------------------------------------

    def stop_animation(self):
        self.running = False
        self.paused = False

        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except tk.TclError:
                pass

        self.after_id = None

    def change_maze(self):
        self.stop_animation()

        size_text = self.size_var.get()
        self.rows = int(size_text.split("x")[0].strip())
        self.cols = self.rows

        self.maze = generate_maze(self.rows)

        self.result = None
        self.frame_index = 0
        self.path_index = 0
        self.visited_positions = set()
        self.visible_path = []
        self.current_position = None
        self.phase = "idle"

        self.distance_label.config(text="—")
        self.explored_label.config(text="0")
        self.keys_label.config(text="None")
        self.status_label.config(text="Ready")

        self.message_label.config(
            text="New maze generated! Click Solve Maze to begin."
        )

        self.draw_maze()

    def reset_maze(self):
        self.stop_animation()

        self.result = None
        self.frame_index = 0
        self.path_index = 0
        self.visited_positions = set()
        self.visible_path = []
        self.current_position = None
        self.phase = "idle"

        self.distance_label.config(text="—")
        self.explored_label.config(text="0")
        self.keys_label.config(text="None")
        self.status_label.config(text="Ready")

        self.message_label.config(
            text="Maze reset. Solve it again or generate a new maze."
        )

        self.draw_maze()

    # -----------------------------------------------------
    # SOLVE AND ANIMATE
    # -----------------------------------------------------

    def start_solve(self):
        self.stop_animation()

        self.result = solve_bfs(self.maze)

        if self.result is None:
            messagebox.showerror("Maze error", "The maze has no start cell.")
            return

        self.frame_index = 0
        self.path_index = 0
        self.visited_positions = set()
        self.visible_path = []
        self.current_position = None
        self.phase = "search"
        self.running = True

        self.distance_label.config(text="Searching...")
        self.explored_label.config(text="0")
        self.keys_label.config(text="Pending")
        self.status_label.config(text="Searching")

        self.message_label.config(text="BFS is exploring the maze...")
        self.animate_step()

    def toggle_pause(self):
        if not self.running:
            return

        self.paused = not self.paused

        if self.paused:
            self.status_label.config(text="Paused")
            self.message_label.config(text="Animation paused.")
        else:
            self.status_label.config(text="Searching")
            self.message_label.config(text="Animation resumed.")
            self.schedule_step()

    def schedule_step(self):
        if self.running and not self.paused:
            delay = max(10, self.speed_var.get())
            self.after_id = self.root.after(delay, self.animate_step)

    def animate_step(self):
        self.after_id = None

        if not self.running or self.paused:
            return

        if self.phase == "search":
            frames = self.result["frames"]

            if self.frame_index < len(frames):
                state, distance = frames[self.frame_index]
                r, c, keys = state

                self.current_position = (r, c)
                self.visited_positions.add((r, c))

                self.explored_label.config(
                    text=str(len(self.visited_positions))
                )
                self.keys_label.config(text=inventory_text(keys))
                self.status_label.config(text="Exploring")
                self.message_label.config(
                    text=f"Exploring cell ({r}, {c}) | Distance: {distance}"
                )

                self.frame_index += 1
                self.draw_maze()
                self.schedule_step()
                return

            # The search is complete. Show the shortest path next.
            if self.result["distance"] == -1:
                self.finish_no_path()
                return

            self.phase = "path"
            self.path_index = 0
            self.visible_path = []

        if self.phase == "path":
            path = self.result["path"]

            if self.path_index < len(path):
                self.visible_path.append(path[self.path_index])
                self.current_position = path[self.path_index]

                self.status_label.config(text="Showing path")
                self.message_label.config(
                    text=f"Shortest path: step {self.path_index} "
                         f"of {len(path) - 1}"
                )

                self.path_index += 1
                self.draw_maze()
                self.schedule_step()
                return

            self.finish_success()

    def finish_no_path(self):
        self.running = False
        self.phase = "done"

        self.distance_label.config(text="-1")
        self.explored_label.config(text=str(self.result["visited_count"]))
        self.keys_label.config(text="None")
        self.status_label.config(text="No route")

        self.message_label.config(
            text="No valid route exists in this maze."
        )

    def finish_success(self):
        self.running = False
        self.phase = "done"

        self.distance_label.config(text=str(self.result["distance"]))
        self.explored_label.config(text=str(self.result["visited_count"]))
        self.keys_label.config(text=inventory_text(self.result["keys"]))
        self.status_label.config(text="Solved!")

        self.message_label.config(
            text="Shortest path found! You can export the result to CSV."
        )

        self.draw_maze()

    # -----------------------------------------------------
    # DRAW MAZE
    # -----------------------------------------------------

    def draw_maze(self):
        if not self.maze:
            return

        self.canvas.delete("all")

        canvas_w = max(100, self.canvas.winfo_width())
        canvas_h = max(100, self.canvas.winfo_height())

        cell_size = min(
            (canvas_w - 30) / self.cols,
            (canvas_h - 30) / self.rows,
        )

        cell_size = max(8, cell_size)

        total_w = cell_size * self.cols
        total_h = cell_size * self.rows

        x_offset = (canvas_w - total_w) / 2
        y_offset = (canvas_h - total_h) / 2

        path_set = set(self.visible_path)

        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.maze[r][c]

                x1 = x_offset + c * cell_size
                y1 = y_offset + r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                color = CELL_COLORS.get(cell, "#FFFFFF")

                if (r, c) in self.visited_positions and cell not in ("S", "E"):
                    color = "#FFE08A"

                if (r, c) in path_set:
                    color = "#FF8A32"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="#D7E3ED",
                    width=1,
                )

                if cell != "." and cell != "#":
                    text_color = "#FFFFFF" if cell in ("S", "E") else "#173B58"

                    self.canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=cell,
                        fill=text_color,
                        font=("Segoe UI", max(7, int(cell_size * 0.38)), "bold"),
                    )

                if (r, c) == self.current_position:
                    margin = max(2, cell_size * 0.10)

                    self.canvas.create_rectangle(
                        x1 + margin, y1 + margin,
                        x2 - margin, y2 - margin,
                        outline="#1769AA",
                        width=max(2, int(cell_size * 0.08)),
                    )

    # -----------------------------------------------------
    # EXPORT CSV
    # -----------------------------------------------------

    def export_csv(self):
        if not self.result or not self.result["path"]:
            messagebox.showinfo(
                "Nothing to export",
                "Solve the maze first to generate a shortest path."
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Save solved maze",
            defaultextension=".csv",
            initialfile="path_grid.csv",
            filetypes=[("CSV files", "*.csv")],
        )

        if not filename:
            return

        path = set(self.result["path"])
        output = []

        for r in range(self.rows):
            row = []

            for c in range(self.cols):
                cell = self.maze[r][c]

                if (r, c) in path:
                    row.append("x" + cell if cell != "." else "x")
                else:
                    row.append(cell)

            output.append(row)

        try:
            with open(filename, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(output)

            messagebox.showinfo(
                "Export complete",
                f"Solved maze saved successfully:\n{filename}"
            )

        except OSError as error:
            messagebox.showerror("Export failed", str(error))


# =========================================================
# 4. RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = MazeApp(root)
    root.mainloop()
