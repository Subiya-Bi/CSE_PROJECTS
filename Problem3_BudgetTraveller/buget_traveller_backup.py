
import csv
import heapq
import time
import tkinter as tk
from tkinter import ttk, messagebox
from statistics import median
from pathlib import Path


# -------------------- FILE PATHS --------------------

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "travel_input.csv"
OUTPUT_FILE = BASE_DIR / "budget_route.csv"


# -------------------- READ FLIGHT DATA --------------------

def load_input():
    flights = []

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Flight data file not found:\n{INPUT_FILE}"
        )

    with open(
        INPUT_FILE, "r", newline="", encoding="utf-8-sig"
    ) as file:
        # Ignore blank lines, including a blank line before the header.
        lines = (line for line in file if line.strip())
        reader = csv.DictReader(lines)

        required = {"RecordType", "From", "To", "Price"}

        if not reader.fieldnames:
            raise ValueError("The CSV file is empty or has no header.")

        reader.fieldnames = [
            (name or "").strip().lstrip("\ufeff")
            for name in reader.fieldnames
        ]

        missing = required - set(reader.fieldnames)

        if missing:
            raise ValueError(
                f"Missing CSV headings: {sorted(missing)}"
            )

        for line_no, row in enumerate(reader, start=2):
            kind = (row.get("RecordType") or "").strip().upper()

            # Journey settings are entered in the dashboard.
            # Only FLIGHT rows are needed from the CSV.
            if kind != "FLIGHT":
                continue

            start = (row.get("From") or "").strip()
            end = (row.get("To") or "").strip()

            try:
                price = int(row["Price"])
            except (ValueError, TypeError, KeyError):
                raise ValueError(
                    f"Invalid flight price near CSV line {line_no}."
                )

            if not start or not end:
                raise ValueError(
                    f"Missing city near CSV line {line_no}."
                )

            if price < 0:
                raise ValueError(
                    f"Flight price cannot be negative near line {line_no}."
                )

            flights.append((start, end, price))

    if not flights:
        raise ValueError(
            "No flights found. Add FLIGHT rows to travel_input.csv."
        )

    cities = sorted({
        city
        for start, end, price in flights
        for city in (start, end)
    })

    return flights, cities


# -------------------- ALGORITHM 1: DYNAMIC PROGRAMMING --------------------

def dynamic_programming(
    cities, flights, source, destination, max_stops, coupons
):
    max_flights = max_stops + 1

    # dp[f][(city, coupons_used)] = minimum cost
    dp = [dict() for _ in range(max_flights + 1)]
    parent = {}

    dp[0][(source, 0)] = 0

    for f in range(1, max_flights + 1):
        for start, end, price in flights:
            for used in range(coupons + 1):
                previous = dp[f - 1].get((start, used))

                if previous is None:
                    continue

                # Option 1: Pay the full flight price.
                normal_cost = previous + price
                state = (end, used)

                if normal_cost < dp[f].get(state, float("inf")):
                    dp[f][state] = normal_cost
                    parent[(f, end, used)] = (
                        f - 1, start, used, price, False
                    )

                # Option 2: Apply a coupon for a 50% discount.
                if used < coupons:
                    discounted_cost = previous + price // 2
                    discounted_state = (end, used + 1)

                    if discounted_cost < dp[f].get(
                        discounted_state, float("inf")
                    ):
                        dp[f][discounted_state] = discounted_cost
                        parent[(f, end, used + 1)] = (
                            f - 1, start, used, price, True
                        )

    best_state = None
    best_cost = float("inf")

    for f in range(max_flights + 1):
        for used in range(coupons + 1):
            cost = dp[f].get(
                (destination, used), float("inf")
            )

            if cost < best_cost:
                best_cost = cost
                best_state = (f, destination, used)

    if best_state is None:
        return None

    route = []
    state = best_state

    while state[0] > 0:
        previous = parent[state]
        prev_f, start, prev_used, price, coupon_used = previous
        current_city = state[1]

        route.append({
            "from": start,
            "to": current_city,
            "original": price,
            "paid": price // 2 if coupon_used else price,
            "coupon": coupon_used
        })

        state = (prev_f, start, prev_used)

    route.reverse()

    return {"cost": best_cost, "route": route}


# -------------------- ALGORITHM 2: DIJKSTRA --------------------

def dijkstra_with_coupons(
    cities, flights, source, destination, max_stops, coupons
):
    graph = {city: [] for city in cities}

    for start, end, price in flights:
        graph[start].append((end, price))

    max_flights = max_stops + 1

    initial = (source, 0, 0)
    distances = {initial: 0}
    parent = {}
    queue = [(0, source, 0, 0)]
    final_state = None

    while queue:
        cost, city, f, used = heapq.heappop(queue)
        state = (city, f, used)

        if cost != distances.get(state):
            continue

        if city == destination:
            final_state = state
            break

        if f >= max_flights:
            continue

        for next_city, price in graph[city]:
            options = [(used, price, False)]

            if used < coupons:
                options.append((used + 1, price // 2, True))

            for next_used, paid, coupon_used in options:
                next_state = (next_city, f + 1, next_used)
                next_cost = cost + paid

                if next_cost < distances.get(
                    next_state, float("inf")
                ):
                    distances[next_state] = next_cost
                    parent[next_state] = (
                        state, price, paid, coupon_used
                    )

                    heapq.heappush(
                        queue,
                        (next_cost, next_city, f + 1, next_used)
                    )

    if final_state is None:
        return None

    route = []
    state = final_state

    while state != initial:
        previous, original, paid, coupon_used = parent[state]

        route.append({
            "from": previous[0],
            "to": state[0],
            "original": original,
            "paid": paid,
            "coupon": coupon_used
        })

        state = previous

    route.reverse()

    return {
        "cost": distances[final_state],
        "route": route
    }


# -------------------- EXPORT ROUTE TO CSV --------------------

def export_route(result):
    with open(
        OUTPUT_FILE, "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)

        writer.writerow([
            "From", "To", "Original Price",
            "Paid Price", "Coupon Used"
        ])

        if result is not None:
            for flight in result["route"]:
                writer.writerow([
                    flight["from"],
                    flight["to"],
                    flight["original"],
                    flight["paid"],
                    "Yes" if flight["coupon"] else "No"
                ])


# -------------------- DASHBOARD --------------------

def show_dashboard(flights, cities):
    root = tk.Tk()
    root.title("Budget Traveller | Route Optimizer")
    root.geometry("1080x780")
    root.minsize(880, 680)
    root.configure(bg="#F3F6FB")

    navy = "#152746"
    blue = "#2563EB"
    green = "#16845B"
    muted = "#63738A"
    white = "#FFFFFF"

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(
        "Treeview",
        rowheight=28,
        background=white,
        fieldbackground=white,
        font=("Segoe UI", 10)
    )

    style.configure(
        "Treeview.Heading",
        font=("Segoe UI", 10, "bold"),
        background="#E8EEF7",
        foreground=navy
    )

    # Header
    header = tk.Frame(root, bg=navy, padx=24, pady=17)
    header.pack(fill="x")

    tk.Label(
        header,
        text="BUDGET TRAVELLER",
        bg=navy,
        fg=white,
        font=("Segoe UI", 22, "bold")
    ).pack(anchor="w")

    tk.Label(
        header,
        text="Intelligent route planning with discount coupons",
        bg=navy,
        fg="#C9D8F0",
        font=("Segoe UI", 10)
    ).pack(anchor="w", pady=(4, 0))

    body = tk.Frame(root, bg="#F3F6FB", padx=20, pady=14)
    body.pack(fill="both", expand=True)

    # User input panel
    input_box = tk.Frame(
        body,
        bg=white,
        padx=16,
        pady=13,
        highlightbackground="#E0E7F0",
        highlightthickness=1
    )
    input_box.pack(fill="x", pady=(0, 12))

    tk.Label(
        input_box,
        text="PLAN YOUR JOURNEY",
        bg=white,
        fg=navy,
        font=("Segoe UI", 12, "bold")
    ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

    input_labels = [
        "Source city",
        "Destination city",
        "Maximum stops",
        "Number of coupons"
    ]

    for col, label in enumerate(input_labels):
        tk.Label(
            input_box,
            text=label,
            bg=white,
            fg=muted,
            font=("Segoe UI", 9)
        ).grid(row=1, column=col, sticky="w", padx=5)

    source_box = ttk.Combobox(
        input_box,
        values=cities,
        state="readonly",
        font=("Segoe UI", 10)
    )

    destination_box = ttk.Combobox(
        input_box,
        values=cities,
        state="readonly",
        font=("Segoe UI", 10)
    )

    stops_entry = ttk.Entry(input_box, font=("Segoe UI", 10))
    coupons_entry = ttk.Entry(input_box, font=("Segoe UI", 10))

    source_box.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
    destination_box.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
    stops_entry.grid(row=2, column=2, padx=5, pady=5, sticky="ew")
    coupons_entry.grid(row=2, column=3, padx=5, pady=5, sticky="ew")

    source_box.set("Bangalore" if "Bangalore" in cities else cities[0])
    destination_box.set("Kolkata" if "Kolkata" in cities else cities[-1])

    stops_entry.insert(0, "3")
    coupons_entry.insert(0, "2")

    for col in range(4):
        input_box.columnconfigure(col, weight=1)

    # Journey result panel
    result_box = tk.Frame(
        body,
        bg=white,
        padx=16,
        pady=12,
        highlightbackground="#E0E7F0",
        highlightthickness=1
    )
    result_box.pack(fill="x", pady=(0, 12))

    tk.Label(
        result_box,
        text="CHEAPEST JOURNEY",
        bg=white,
        fg=navy,
        font=("Segoe UI", 12, "bold")
    ).pack(anchor="w")

    cost_label = tk.Label(
        result_box,
        text="Enter your journey and click Find Cheapest Route",
        bg=white,
        fg=green,
        font=("Segoe UI", 19, "bold"),
        wraplength=950,
        justify="left"
    )
    cost_label.pack(anchor="w", pady=(6, 3))

    route_label = tk.Label(
        result_box,
        text="Your route will appear here.",
        bg=white,
        fg=navy,
        font=("Segoe UI", 11),
        wraplength=950,
        justify="left"
    )
    route_label.pack(anchor="w")

    savings_label = tk.Label(
        result_box,
        text="",
        bg=white,
        fg=green,
        font=("Segoe UI", 10, "bold")
    )
    savings_label.pack(anchor="w", pady=(4, 0))

    # Table and graph area
    middle = tk.Frame(body, bg="#F3F6FB")
    middle.pack(fill="both", expand=True)

    table_frame = tk.Frame(
        middle, bg=white, padx=10, pady=10
    )
    table_frame.pack(
        side="left", fill="both", expand=True, padx=(0, 8)
    )

    tk.Label(
        table_frame,
        text="FLIGHT BREAKDOWN",
        bg=white,
        fg=navy,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w", pady=(0, 8))

    columns = ("start", "end", "original", "paid", "coupon")

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=8
    )

    for column, heading in [
        ("start", "From"),
        ("end", "To"),
        ("original", "Original ₹"),
        ("paid", "Paid ₹"),
        ("coupon", "Coupon")
    ]:
        tree.heading(column, text=heading)
        tree.column(column, width=85, anchor="center")

    tree.pack(fill="both", expand=True)

    chart_frame = tk.Frame(
        middle, bg=white, padx=10, pady=10
    )
    chart_frame.pack(side="right", fill="both", expand=True)

    tk.Label(
        chart_frame,
        text="ALGORITHM PERFORMANCE",
        bg=white,
        fg=navy,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w")

    chart = tk.Canvas(
        chart_frame,
        bg=white,
        height=210,
        highlightthickness=0
    )
    chart.pack(fill="both", expand=True, pady=8)

    timing_label = tk.Label(
        chart_frame,
        text="Run a search to compare both algorithms.",
        bg=white,
        fg=muted,
        font=("Segoe UI", 9)
    )
    timing_label.pack(anchor="w")

    performance = {"dp": 0.0, "dijkstra": 0.0}
    latest_result = {"result": None}

    # Draw the algorithm comparison graph.
    def draw_chart(event=None):
        chart.delete("all")

        width = max(chart.winfo_width(), 280)

        values = [
            performance["dp"],
            performance["dijkstra"]
        ]

        labels = [
            "Dynamic Programming",
            "Dijkstra"
        ]

        colors = [blue, green]
        maximum = max(max(values), 0.01)

        for index, (value, label, color) in enumerate(
            zip(values, labels, colors)
        ):
            y = 32 + index * 78

            chart.create_text(
                8, y,
                text=label,
                anchor="w",
                fill=navy,
                font=("Segoe UI", 9)
            )

            available_width = max(width - 100, 10)
            bar_width = available_width * value / maximum

            chart.create_rectangle(
                8,
                y + 20,
                8 + max(bar_width, 2),
                y + 42,
                fill=color,
                outline=""
            )

            chart.create_text(
                width - 8,
                y + 56,
                text=f"{value:.3f} ms",
                anchor="e",
                fill=muted,
                font=("Segoe UI", 9)
            )

    chart.bind("<Configure>", draw_chart)

    # Calculate the cheapest route after the button is clicked.
    def find_route():
        source = source_box.get().strip()
        destination = destination_box.get().strip()

        try:
            max_stops = int(stops_entry.get().strip())
            coupons = int(coupons_entry.get().strip())

            if not source or not destination:
                raise ValueError("Select both source and destination.")

            if source not in cities or destination not in cities:
                raise ValueError(
                    "Select cities available in the flight data."
                )

            if max_stops < 0 or coupons < 0:
                raise ValueError(
                    "Stops and coupons cannot be negative."
                )

        except ValueError as error:
            messagebox.showerror("Invalid input", str(error))
            return

        dp_times = []
        dij_times = []
        dp_result = None
        dij_result = None

        try:
            # Run each algorithm five times for a more stable comparison.
            for _ in range(5):
                start_time = time.perf_counter()

                dp_result = dynamic_programming(
                    cities,
                    flights,
                    source,
                    destination,
                    max_stops,
                    coupons
                )

                dp_times.append(
                    (time.perf_counter() - start_time) * 1000
                )

                start_time = time.perf_counter()

                dij_result = dijkstra_with_coupons(
                    cities,
                    flights,
                    source,
                    destination,
                    max_stops,
                    coupons
                )

                dij_times.append(
                    (time.perf_counter() - start_time) * 1000
                )

            dp_ms = median(dp_times)
            dij_ms = median(dij_times)

            if (
                (dp_result is None) != (dij_result is None)
                or (
                    dp_result is not None
                    and dp_result["cost"] != dij_result["cost"]
                )
            ):
                raise RuntimeError(
                    "The algorithms returned different results."
                )

        except (ValueError, RuntimeError, KeyError) as error:
            messagebox.showerror("Calculation error", str(error))
            return

        performance["dp"] = dp_ms
        performance["dijkstra"] = dij_ms
        latest_result["result"] = dp_result

        draw_chart()

        for item in tree.get_children():
            tree.delete(item)

        if dp_result is None:
            cost_label.config(
                text="No valid route found within this stop limit.",
                fg="#B42318"
            )

            route_label.config(text="")
            savings_label.config(text="")
        else:
            route = dp_result["route"]

            cost_label.config(
                text=f"Total cost: ₹{dp_result['cost']:,}",
                fg=green
            )

            path = [source] + [
                flight["to"] for flight in route
            ]

            route_label.config(text="  →  ".join(path))

            original_total = sum(
                flight["original"] for flight in route
            )

            savings = original_total - dp_result["cost"]

            savings_label.config(
                text=f"Coupon savings: ₹{savings:,}   |   "
                     f"Flights: {len(route)}"
            )

            for flight in route:
                tree.insert(
                    "",
                    "end",
                    values=(
                        flight["from"],
                        flight["to"],
                        flight["original"],
                        flight["paid"],
                        "Yes" if flight["coupon"] else "No"
                    )
                )

        timing_label.config(
            text=f"Dynamic Programming: {dp_ms:.3f} ms   |   "
                 f"Dijkstra: {dij_ms:.3f} ms"
        )

    # Export the most recent result.
    def save_route():
        try:
            export_route(latest_result["result"])
            messagebox.showinfo(
                "Export complete",
                f"Route saved to:\n{OUTPUT_FILE}"
            )
        except OSError as error:
            messagebox.showerror("Export error", str(error))

    # Footer buttons
    footer = tk.Frame(body, bg="#F3F6FB")
    footer.pack(fill="x", pady=(12, 0))

    tk.Button(
        footer,
        text="Find Cheapest Route",
        command=find_route,
        bg=blue,
        fg=white,
        activebackground="#1D4ED8",
        activeforeground=white,
        relief="flat",
        padx=18,
        pady=10,
        font=("Segoe UI", 10, "bold")
    ).pack(side="left")

    tk.Button(
        footer,
        text="Export Route CSV",
        command=save_route,
        bg=green,
        fg=white,
        activebackground="#116B49",
        activeforeground=white,
        relief="flat",
        padx=14,
        pady=10,
        font=("Segoe UI", 10, "bold")
    ).pack(side="left", padx=8)

    tk.Label(
        footer,
        text=f"{len(flights)} available flights",
        bg="#F3F6FB",
        fg=muted,
        font=("Segoe UI", 9)
    ).pack(side="right")

    root.after(200, draw_chart)
    root.mainloop()


# -------------------- MAIN PROGRAM --------------------

def main():
    flights, cities = load_input()
    show_dashboard(flights, cities)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print(f"\nInput error: {error}")
        input("Press Enter to exit...")
