
import csv
import heapq
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from statistics import median
from pathlib import Path

# ============================================================
# BUDGET TRAVELLER PRO
# Dynamic Programming + Dijkstra + Coupon Optimization
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "travel_input.csv"

BG = "#F3F6FB"
NAVY = "#152746"
BLUE = "#2563EB"
GREEN = "#16845B"
ORANGE = "#D97706"
RED = "#B42318"
WHITE = "#FFFFFF"
MUTED = "#63738A"
BORDER = "#DFE7F1"


# -------------------- LOAD FLIGHT DATA --------------------

def load_input():
    flights = []

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Flight data file not found:\n{INPUT_FILE}"
        )

    with open(
        INPUT_FILE, "r", newline="", encoding="utf-8-sig"
    ) as file:
        lines = (line for line in file if line.strip())
        reader = csv.DictReader(lines)

        if not reader.fieldnames:
            raise ValueError("CSV file has no header.")

        reader.fieldnames = [
            (name or "").strip().lstrip("\ufeff")
            for name in reader.fieldnames
        ]

        required = {"RecordType", "From", "To", "Price"}
        missing = required - set(reader.fieldnames)

        if missing:
            raise ValueError(
                f"Missing CSV headings: {', '.join(sorted(missing))}"
            )

        for line_no, row in enumerate(reader, start=2):
            kind = (
                row.get("RecordType") or ""
            ).strip().upper()

            if kind != "FLIGHT":
                continue

            start = (row.get("From") or "").strip()
            end = (row.get("To") or "").strip()

            try:
                price = int(row["Price"])
            except (ValueError, TypeError, KeyError):
                raise ValueError(
                    f"Invalid price near CSV line {line_no}."
                )

            if not start or not end:
                raise ValueError(
                    f"Missing city near CSV line {line_no}."
                )

            if price < 0:
                raise ValueError(
                    f"Negative price near CSV line {line_no}."
                )

            flights.append((start, end, price))

    if not flights:
        raise ValueError(
            "No flights found in travel_input.csv."
        )

    cities = sorted({
        city
        for start, end, _ in flights
        for city in (start, end)
    })

    return flights, cities


# -------------------- ALGORITHM 1: DYNAMIC PROGRAMMING --------------------

def dynamic_programming(
    cities, flights, source, destination, max_stops, coupons
):
    if source == destination:
        return {"cost": 0, "route": []}

    max_flights = max_stops + 1
    dp = [dict() for _ in range(max_flights + 1)]
    parent = {}

    dp[0][(source, 0)] = 0

    for f in range(1, max_flights + 1):
        for start, end, price in flights:
            for used in range(coupons + 1):
                previous_cost = dp[f - 1].get((start, used))

                if previous_cost is None:
                    continue

                # Option 1: Full fare
                normal_cost = previous_cost + price
                state = (end, used)

                if normal_cost < dp[f].get(
                    state, float("inf")
                ):
                    dp[f][state] = normal_cost
                    parent[(f, end, used)] = (
                        f - 1, start, used, price, False
                    )

                # Option 2: 50% coupon discount
                if used < coupons:
                    discounted_cost = previous_cost + price // 2
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
        previous = parent.get(state)

        if previous is None:
            return None

        prev_f, start, prev_used, price, coupon_used = previous

        route.append({
            "from": start,
            "to": state[1],
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
    if source == destination:
        return {"cost": 0, "route": []}

    graph = {city: [] for city in cities}

    for start, end, price in flights:
        graph[start].append((end, price))

    max_flights = max_stops + 1

    # State: city, flights taken, coupons used
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

        for next_city, price in graph.get(city, []):
            options = [(used, price, False)]

            if used < coupons:
                options.append((used + 1, price // 2, True))

            for next_used, paid, coupon_used in options:
                next_state = (
                    next_city, f + 1, next_used
                )
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
                        (
                            next_cost, next_city,
                            f + 1, next_used
                        )
                    )

    if final_state is None:
        return None

    route = []
    state = final_state

    while state != initial:
        data = parent.get(state)

        if data is None:
            return None

        previous, original, paid, coupon_used = data

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


# -------------------- CSV EXPORT --------------------

def export_route(result, output_path):
    with open(
        output_path, "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)

        writer.writerow([
            "From", "To", "Original Price",
            "Paid Price", "Coupon Used", "Savings"
        ])

        for flight in result["route"]:
            writer.writerow([
                flight["from"],
                flight["to"],
                flight["original"],
                flight["paid"],
                "Yes" if flight["coupon"] else "No",
                flight["original"] - flight["paid"]
            ])

        writer.writerow([])
        writer.writerow(["Total Cost", result["cost"]])


# -------------------- DASHBOARD --------------------

def show_dashboard(flights, cities):
    root = tk.Tk()
    root.title("Budget Traveller Pro | Route Optimizer")
    root.geometry("1220x900")
    root.minsize(950, 700)
    root.configure(bg=BG)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(
        "Treeview",
        rowheight=29,
        background=WHITE,
        fieldbackground=WHITE,
        foreground=NAVY,
        font=("Segoe UI", 10)
    )

    style.configure(
        "Treeview.Heading",
        background="#E8EEF7",
        foreground=NAVY,
        font=("Segoe UI", 10, "bold")
    )

    # Scrollable page
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True)

    main_canvas = tk.Canvas(
        outer, bg=BG, highlightthickness=0
    )
    scrollbar = ttk.Scrollbar(
        outer, orient="vertical", command=main_canvas.yview
    )
    main_canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    main_canvas.pack(side="left", fill="both", expand=True)

    page = tk.Frame(main_canvas, bg=BG)
    window_id = main_canvas.create_window(
        (0, 0), window=page, anchor="nw"
    )

    def update_scroll_region(event=None):
        main_canvas.configure(
            scrollregion=main_canvas.bbox("all")
        )

    def resize_page(event):
        main_canvas.itemconfigure(
            window_id, width=event.width
        )

    page.bind("<Configure>", update_scroll_region)
    main_canvas.bind("<Configure>", resize_page)

    # Header
    header = tk.Frame(page, bg=NAVY, padx=28, pady=22)
    header.pack(fill="x")

    tk.Label(
        header,
        text="BUDGET TRAVELLER PRO",
        bg=NAVY,
        fg=WHITE,
        font=("Segoe UI", 24, "bold")
    ).pack(anchor="w")

    tk.Label(
        header,
        text="SMART ROUTE OPTIMIZATION  •  COUPON SAVINGS  •  ALGORITHM ANALYSIS",
        bg=NAVY,
        fg="#C9D8F0",
        font=("Segoe UI", 10)
    ).pack(anchor="w", pady=(5, 0))

    body = tk.Frame(page, bg=BG, padx=22, pady=18)
    body.pack(fill="both", expand=True)

    # Input panel
    input_box = tk.Frame(
        body, bg=WHITE, padx=18, pady=16,
        highlightbackground=BORDER, highlightthickness=1
    )
    input_box.pack(fill="x", pady=(0, 14))

    tk.Label(
        input_box,
        text="PLAN YOUR JOURNEY",
        bg=WHITE,
        fg=NAVY,
        font=("Segoe UI", 13, "bold")
    ).grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 13))

    labels = [
        "Source city",
        "Destination city",
        "Maximum stops",
        "Available coupons",
        "Your budget (₹)"
    ]

    for col, label in enumerate(labels):
        tk.Label(
            input_box,
            text=label,
            bg=WHITE,
            fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).grid(row=1, column=col, sticky="w", padx=5)

    source_box = ttk.Combobox(
        input_box, values=cities, state="readonly"
    )
    destination_box = ttk.Combobox(
        input_box, values=cities, state="readonly"
    )
    stops_entry = ttk.Entry(input_box)
    coupons_entry = ttk.Entry(input_box)
    budget_entry = ttk.Entry(input_box)

    widgets = [
        source_box, destination_box, stops_entry,
        coupons_entry, budget_entry
    ]

    for col, widget in enumerate(widgets):
        widget.grid(
            row=2, column=col, sticky="ew",
            padx=5, pady=(5, 10), ipady=5
        )
        input_box.columnconfigure(col, weight=1)

    source_box.set(
        "Bangalore" if "Bangalore" in cities else cities[0]
    )
    destination_box.set(
        "Kolkata" if "Kolkata" in cities else cities[-1]
    )
    stops_entry.insert(0, "3")
    coupons_entry.insert(0, "2")
    budget_entry.insert(0, "1000")

    tk.Label(
        input_box,
        text="A stop is an intermediate city. Maximum flights = maximum stops + 1. Leave the budget blank for no limit.",
        bg=WHITE,
        fg=MUTED,
        font=("Segoe UI", 9)
    ).grid(row=3, column=0, columnspan=5, sticky="w", padx=5)

    # Summary cards
    cards_frame = tk.Frame(body, bg=BG)
    cards_frame.pack(fill="x", pady=(0, 14))

    card_data = [
        ("TOTAL FARE", "₹—", BLUE),
        ("YOU SAVE", "₹—", GREEN),
        ("FLIGHTS", "—", ORANGE),
        ("COUPONS USED", "—", NAVY)
    ]

    card_values = []

    for title, initial, accent in card_data:
        card = tk.Frame(
            cards_frame, bg=WHITE, padx=15, pady=14,
            highlightbackground=BORDER, highlightthickness=1
        )
        card.pack(
            side="left", fill="both", expand=True,
            padx=(0, 9)
        )

        tk.Label(
            card, text=title, bg=WHITE, fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        value_label = tk.Label(
            card, text=initial, bg=WHITE, fg=accent,
            font=("Segoe UI", 21, "bold")
        )
        value_label.pack(anchor="w", pady=(6, 0))
        card_values.append(value_label)

    # Journey summary
    result_box = tk.Frame(
        body, bg=WHITE, padx=18, pady=15,
        highlightbackground=BORDER, highlightthickness=1
    )
    result_box.pack(fill="x", pady=(0, 14))

    tk.Label(
        result_box, text="CHEAPEST JOURNEY",
        bg=WHITE, fg=NAVY,
        font=("Segoe UI", 12, "bold")
    ).pack(anchor="w")

    cost_label = tk.Label(
        result_box,
        text="Choose your journey and click Find Cheapest Route.",
        bg=WHITE, fg=GREEN,
        font=("Segoe UI", 17, "bold"),
        wraplength=1050, justify="left"
    )
    cost_label.pack(anchor="w", pady=(8, 5))

    route_label = tk.Label(
        result_box,
        text="Your selected route will appear here.",
        bg=WHITE, fg=NAVY,
        font=("Segoe UI", 11),
        wraplength=1050, justify="left"
    )
    route_label.pack(anchor="w")

    savings_label = tk.Label(
        result_box, text="", bg=WHITE, fg=GREEN,
        font=("Segoe UI", 10, "bold"),
        wraplength=1050, justify="left"
    )
    savings_label.pack(anchor="w", pady=(5, 0))

    # Route map
    map_box = tk.Frame(
        body, bg=WHITE, padx=14, pady=12,
        highlightbackground=BORDER, highlightthickness=1
    )
    map_box.pack(fill="x", pady=(0, 14))

    tk.Label(
        map_box, text="VISUAL ROUTE MAP",
        bg=WHITE, fg=NAVY,
        font=("Segoe UI", 12, "bold")
    ).pack(anchor="w", pady=(0, 8))

    route_canvas = tk.Canvas(
        map_box, bg="#FBFDFF", height=175,
        highlightthickness=0
    )
    route_canvas.pack(fill="x", expand=True)

    latest_result = {"result": None}
    latest_route = {"source": "", "destination": ""}
    performance = {"dp": 0.0, "dijkstra": 0.0}

    def draw_route(route, source, destination):
        route_canvas.delete("all")
        width = max(route_canvas.winfo_width(), 500)
        height = 175

        if route is None:
            route_canvas.create_text(
                width // 2, height // 2,
                text="Find a valid journey to display its route.",
                fill=MUTED, font=("Segoe UI", 10)
            )
            return

        if not route:
            route_canvas.create_oval(
                width // 2 - 24, 48,
                width // 2 + 24, 96,
                fill=BLUE, outline=""
            )
            route_canvas.create_text(
                width // 2, 72,
                text=source[:8], fill=WHITE,
                font=("Segoe UI", 8, "bold")
            )
            route_canvas.create_text(
                width // 2, 120,
                text="Source and destination are the same",
                fill=NAVY, font=("Segoe UI", 9)
            )
            return

        path = [source] + [flight["to"] for flight in route]
        count = len(path)
        margin = 65

        positions = (
            [width / 2] if count == 1 else
            [
                margin + i * (width - 2 * margin) / (count - 1)
                for i in range(count)
            ]
        )

        y = 72

        for i, flight in enumerate(route):
            route_canvas.create_line(
                positions[i], y,
                positions[i + 1], y,
                fill="#A8BDE3", width=3, arrow=tk.LAST
            )

            mid_x = (positions[i] + positions[i + 1]) / 2
            fare = f"₹{flight['paid']:,}"

            if flight["coupon"]:
                fare += " *"

            route_canvas.create_text(
                mid_x, y - 24, text=fare,
                fill=GREEN if flight["coupon"] else NAVY,
                font=("Segoe UI", 9, "bold")
            )

        for i, city in enumerate(path):
            x = positions[i]
            fill = GREEN if i == count - 1 else BLUE

            route_canvas.create_oval(
                x - 23, y - 23, x + 23, y + 23,
                fill=fill, outline=""
            )
            route_canvas.create_text(
                x, y, text=city[:8], fill=WHITE,
                font=("Segoe UI", 8, "bold")
            )

            label = (
                "Start" if i == 0 else
                "Destination" if i == count - 1 else
                f"Stop {i}"
            )

            route_canvas.create_text(
                x, y + 39, text=label,
                fill=MUTED, font=("Segoe UI", 8)
            )

        route_canvas.create_text(
            width - 8, height - 8,
            text="* Discounted fare", anchor="se",
            fill=GREEN, font=("Segoe UI", 8)
        )

    # Flight breakdown table
    middle = tk.Frame(body, bg=BG)
    middle.pack(fill="both", expand=True)

    table_frame = tk.Frame(
        middle, bg=WHITE, padx=12, pady=12,
        highlightbackground=BORDER, highlightthickness=1
    )
    table_frame.pack(
        side="left", fill="both", expand=True,
        padx=(0, 8)
    )

    tk.Label(
        table_frame, text="FLIGHT-BY-FLIGHT BREAKDOWN",
        bg=WHITE, fg=NAVY,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w", pady=(0, 8))

    columns = (
        "start", "end", "original", "paid", "saving", "coupon"
    )

    tree = ttk.Treeview(
        table_frame, columns=columns,
        show="headings", height=7
    )

    for column, heading in [
        ("start", "From"),
        ("end", "To"),
        ("original", "Original ₹"),
        ("paid", "Paid ₹"),
        ("saving", "Saved ₹"),
        ("coupon", "Coupon")
    ]:
        tree.heading(column, text=heading)
        tree.column(column, width=85, anchor="center")

    tree.pack(fill="both", expand=True)
    tree.tag_configure("discounted", foreground=GREEN)

    # Algorithm performance panel
    performance_frame = tk.Frame(
        middle, bg=WHITE, padx=12, pady=12,
        highlightbackground=BORDER, highlightthickness=1
    )
    performance_frame.pack(
        side="right", fill="both", expand=True
    )

    tk.Label(
        performance_frame, text="ALGORITHM PERFORMANCE",
        bg=WHITE, fg=NAVY,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w")

    tk.Label(
        performance_frame,
        text="Median runtime from five measurements",
        bg=WHITE, fg=MUTED,
        font=("Segoe UI", 9)
    ).pack(anchor="w", pady=(3, 5))

    chart = tk.Canvas(
        performance_frame, bg=WHITE, height=145,
        highlightthickness=0
    )
    chart.pack(fill="both", expand=True)

    timing_label = tk.Label(
        performance_frame,
        text="Run a search to compare the algorithms.",
        bg=WHITE, fg=MUTED,
        font=("Segoe UI", 9), justify="left"
    )
    timing_label.pack(anchor="w", pady=(5, 0))

    correctness_label = tk.Label(
        performance_frame,
        text="Correctness: not tested yet",
        bg=WHITE, fg=MUTED,
        font=("Segoe UI", 9, "bold")
    )
    correctness_label.pack(anchor="w", pady=(5, 0))

    def draw_chart(event=None):
        chart.delete("all")
        width = max(chart.winfo_width(), 300)

        values = [
            performance["dp"], performance["dijkstra"]
        ]
        labels = ["Dynamic Programming", "Dijkstra"]
        colors = [BLUE, GREEN]
        maximum = max(max(values), 0.001)

        for i, (value, label, color) in enumerate(
            zip(values, labels, colors)
        ):
            y = 23 + i * 65

            chart.create_text(
                5, y, text=label, anchor="w",
                fill=NAVY, font=("Segoe UI", 9, "bold")
            )

            available_width = max(width - 25, 10)
            bar_width = available_width * value / maximum

            chart.create_rectangle(
                5, y + 19, 5 + max(bar_width, 2), y + 35,
                fill=color, outline=""
            )

            chart.create_text(
                width - 5, y + 48,
                text=f"{value:.4f} ms", anchor="e",
                fill=MUTED, font=("Segoe UI", 9)
            )

    chart.bind("<Configure>", draw_chart)

    # -------------------- FIND ROUTE --------------------

    def find_route():
        source = source_box.get().strip()
        destination = destination_box.get().strip()

        try:
            max_stops = int(stops_entry.get().strip())
            coupons = int(coupons_entry.get().strip())

            budget_text = budget_entry.get().strip()
            budget = int(budget_text) if budget_text else None

            if source not in cities or destination not in cities:
                raise ValueError(
                    "Select a valid source and destination."
                )

            if not 0 <= max_stops <= 100:
                raise ValueError(
                    "Maximum stops must be between 0 and 100."
                )

            if not 0 <= coupons <= 50:
                raise ValueError(
                    "Coupons must be between 0 and 50."
                )

            if budget is not None and budget < 0:
                raise ValueError("Budget cannot be negative.")

        except ValueError as error:
            messagebox.showerror("Invalid input", str(error))
            return

        dp_times = []
        dijkstra_times = []

        # Warm-up before benchmarking.
        dynamic_programming(
            cities, flights, source, destination,
            max_stops, coupons
        )
        dijkstra_with_coupons(
            cities, flights, source, destination,
            max_stops, coupons
        )

        try:
            for _ in range(5):
                start_time = time.perf_counter()
                dp_result = dynamic_programming(
                    cities, flights, source, destination,
                    max_stops, coupons
                )
                dp_times.append(
                    (time.perf_counter() - start_time) * 1000
                )

                start_time = time.perf_counter()
                dijkstra_result = dijkstra_with_coupons(
                    cities, flights, source, destination,
                    max_stops, coupons
                )
                dijkstra_times.append(
                    (time.perf_counter() - start_time) * 1000
                )

        except (ValueError, KeyError, IndexError) as error:
            messagebox.showerror("Calculation error", str(error))
            return

        dp_ms = median(dp_times)
        dijkstra_ms = median(dijkstra_times)

        performance["dp"] = dp_ms
        performance["dijkstra"] = dijkstra_ms

        same_result = (
            (dp_result is None and dijkstra_result is None)
            or (
                dp_result is not None
                and dijkstra_result is not None
                and dp_result["cost"] == dijkstra_result["cost"]
            )
        )

        if not same_result:
            correctness_label.config(
                text="Correctness: mismatch detected", fg=RED
            )
            messagebox.showerror(
                "Verification failed",
                "The algorithms returned different costs."
            )
            return

        correctness_label.config(
            text="Correctness: both algorithms agree", fg=GREEN
        )

        # Also calculate the cheapest route with no coupons.
        no_coupon_result = dynamic_programming(
            cities, flights, source, destination,
            max_stops, 0
        )

        latest_result["result"] = dp_result
        latest_route["source"] = source
        latest_route["destination"] = destination

        for item in tree.get_children():
            tree.delete(item)

        draw_chart()

        if dp_result is None:
            cost_label.config(
                text="No valid route found within this stop limit.",
                fg=RED
            )
            route_label.config(text="")
            savings_label.config(text="")

            for card in card_values:
                card.config(text="—")

            draw_route(None, source, destination)
            return

        route = dp_result["route"]
        total_cost = dp_result["cost"]

        original_total = sum(
            flight["original"] for flight in route
        )
        total_savings = original_total - total_cost
        flights_used = len(route)
        coupons_used = sum(
            1 for flight in route if flight["coupon"]
        )

        card_values[0].config(text=f"₹{total_cost:,}")
        card_values[1].config(text=f"₹{total_savings:,}")
        card_values[2].config(text=str(flights_used))
        card_values[3].config(text=f"{coupons_used}/{coupons}")

        cost_label.config(
            text=f"Total journey cost: ₹{total_cost:,}",
            fg=GREEN
        )

        route_label.config(
            text="  →  ".join(
                [source] + [flight["to"] for flight in route]
            )
        )

        if no_coupon_result is not None:
            no_coupon_cost = no_coupon_result["cost"]
            baseline_text = (
                f"Cheapest fare without coupons: ₹{no_coupon_cost:,}"
            )
            coupon_savings = no_coupon_cost - total_cost
            baseline_text += (
                f"   |   Savings vs. no-coupon journey: "
                f"₹{coupon_savings:,}"
            )
        else:
            baseline_text = "No route available without coupons."

        if budget is None:
            budget_status = "No budget limit set"
        elif total_cost <= budget:
            budget_status = f"Within budget by ₹{budget - total_cost:,}"
        else:
            budget_status = f"Over budget by ₹{total_cost - budget:,}"

        savings_label.config(
            text=(
                f"Original fare of selected route: ₹{original_total:,}"
                f"   |   Selected-route savings: ₹{total_savings:,}\n"
                f"{baseline_text}\n{budget_status}"
            ),
            fg=(
                GREEN
                if budget is None or total_cost <= budget
                else RED
            )
        )

        for flight in route:
            saving = flight["original"] - flight["paid"]

            tree.insert(
                "",
                "end",
                values=(
                    flight["from"],
                    flight["to"],
                    f"₹{flight['original']:,}",
                    f"₹{flight['paid']:,}",
                    f"₹{saving:,}",
                    "Yes" if flight["coupon"] else "No"
                ),
                tags=(
                    "discounted" if flight["coupon"] else ""
                )
            )

        draw_route(route, source, destination)

        timing_label.config(
            text=(
                f"Dynamic Programming: {dp_ms:.4f} ms\n"
                f"Dijkstra: {dijkstra_ms:.4f} ms\n"
                "Runtime depends on your data and computer."
            )
        )

    # -------------------- EXPORT ROUTE --------------------

    def save_route():
        result = latest_result["result"]

        if result is None:
            messagebox.showwarning(
                "No route to export",
                "Find a valid route before exporting."
            )
            return

        output_path = filedialog.asksaveasfilename(
            title="Save optimized route",
            initialdir=str(BASE_DIR),
            initialfile="budget_route.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not output_path:
            return

        try:
            export_route(result, output_path)
            messagebox.showinfo(
                "Export successful",
                f"Route saved to:\n{output_path}"
            )
        except OSError as error:
            messagebox.showerror("Export error", str(error))

    # -------------------- RESET --------------------

    def reset_form():
        source_box.set(
            "Bangalore" if "Bangalore" in cities else cities[0]
        )
        destination_box.set(
            "Kolkata" if "Kolkata" in cities else cities[-1]
        )

        for entry, value in [
            (stops_entry, "3"),
            (coupons_entry, "2"),
            (budget_entry, "1000")
        ]:
            entry.delete(0, tk.END)
            entry.insert(0, value)

        latest_result["result"] = None
        latest_route["source"] = ""
        latest_route["destination"] = ""

        for card in card_values:
            card.config(text="—")

        cost_label.config(
            text="Choose your journey and click Find Cheapest Route.",
            fg=GREEN
        )
        route_label.config(
            text="Your selected route will appear here."
        )
        savings_label.config(text="")

        for item in tree.get_children():
            tree.delete(item)

        performance["dp"] = 0.0
        performance["dijkstra"] = 0.0

        timing_label.config(
            text="Run a search to compare the algorithms."
        )
        correctness_label.config(
            text="Correctness: not tested yet", fg=MUTED
        )

        draw_chart()
        draw_route(None, "", "")

    # -------------------- FOOTER BUTTONS --------------------

    footer = tk.Frame(body, bg=BG)
    footer.pack(fill="x", pady=(14, 10))

    def make_button(parent, text, command, color):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=WHITE,
            activebackground=color,
            activeforeground=WHITE,
            relief="flat",
            cursor="hand2",
            padx=17,
            pady=10,
            font=("Segoe UI", 10, "bold"),
            borderwidth=0
        )

    make_button(
        footer, "Find Cheapest Route", find_route, BLUE
    ).pack(side="left")

    make_button(
        footer, "Export Route CSV", save_route, GREEN
    ).pack(side="left", padx=8)

    make_button(
        footer, "Reset", reset_form, NAVY
    ).pack(side="left")

    tk.Label(
        footer,
        text=f"{len(cities)} cities  •  {len(flights)} flight connections",
        bg=BG, fg=MUTED,
        font=("Segoe UI", 9)
    ).pack(side="right")

    route_canvas.bind(
        "<Configure>",
        lambda event: draw_route(
            latest_result["result"]["route"]
            if latest_result["result"] is not None
            else None,
            latest_route["source"],
            latest_route["destination"]
        )
    )

    root.after(250, draw_chart)
    root.after(300, lambda: draw_route(None, "", ""))
    root.mainloop()


# -------------------- MAIN --------------------

def main():
    flights, cities = load_input()
    show_dashboard(flights, cities)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print(f"\nInput error: {error}")
        input("Press Enter to exit...")
