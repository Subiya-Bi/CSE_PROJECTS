
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from collections import deque
import csv


# -------------------------------
# 1. DEFINE THE MAZE
# -------------------------------

maze = [
    list("S..#..."),
    list(".a.#A.."),
    list("...#..."),
    list(".#....."),
    list("...b.B."),
    list("###.#.."),
    list("......E")
]

ROWS = len(maze)
COLS = len(maze[0])


# -------------------------------
# 2. KEY REPRESENTATION
# -------------------------------

def key_bit(letter):
    """Return a unique bit for each key a-f."""
    return 1 << (ord(letter.lower()) - ord('a'))


# -------------------------------
# 3. VISUALIZE THE MAZE
# -------------------------------

def visualize_maze(path):
    fig, ax = plt.subplots(figsize=(8, 8))

    colors = {
        '.': '#F4F7FA',   # Empty path
        '#': '#263238',   # Wall
        'S': '#81C784',   # Start
        'E': '#EF5350',   # Exit
        'a': '#64B5F6',   # Key a
        'b': '#4DB6AC',   # Key b
        'c': '#FFD54F',   # Key c
        'd': '#FFCC80',   # Key d
        'e': '#B0BEC5',   # Key e
        'f': '#F48FB1',   # Key f
        'A': '#FFAB91',   # Door A
        'B': '#CE93D8',   # Door B
        'C': '#FFD54F',   # Door C
        'D': '#FFCC80',   # Door D
        'F': '#F48FB1'    # Door F
    }

    path_cells = set(path)

    for r in range(ROWS):
        for c in range(COLS):
            cell = maze[r][c]

            x = c
            y = ROWS - 1 - r

            # Draw the cell.
            rect = Rectangle(
                (x, y), 1, 1,
                facecolor=colors.get(cell, '#F4F7FA'),
                edgecolor='white',
                linewidth=2
            )
            ax.add_patch(rect)

            # Highlight the shortest path.
            if (r, c) in path_cells:
                outline = Rectangle(
                    (x + 0.08, y + 0.08),
                    0.84, 0.84,
                    fill=False,
                    edgecolor='#FF6D00',
                    linewidth=3
                )
                ax.add_patch(outline)

            # Display the cell symbol.
            ax.text(
                x + 0.5,
                y + 0.5,
                cell,
                ha='center',
                va='center',
                fontsize=16,
                fontweight='bold',
                color='white' if cell == '#' else '#263238'
            )

    ax.set_xlim(0, COLS)
    ax.set_ylim(0, ROWS)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])

    ax.set_title(
        f"Maze with Keys and Doors\n"
        f"Shortest Path: {len(path) - 1} moves",
        fontsize=15,
        fontweight='bold',
        pad=15
    )

    # Add a legend.
    legend_items = [
        ("Start", "#81C784"),
        ("Exit", "#EF5350"),
        ("Wall", "#263238"),
        ("Key", "#64B5F6"),
        ("Door", "#CE93D8"),
        ("Shortest path", "#FF6D00")
    ]

    for i, (label, color) in enumerate(legend_items):
        ax.scatter(
            [], [],
            color=color,
            s=100,
            label=label
        )

    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, -0.04),
        ncol=3,
        frameon=False
    )

    plt.tight_layout()
    plt.show()


# -------------------------------
# 4. BREADTH-FIRST SEARCH (BFS)
# -------------------------------

def solve_maze():

    # Find the starting position.
    start = None

    for r in range(ROWS):
        for c in range(COLS):
            if maze[r][c] == 'S':
                start = (r, c)
                break

        if start is not None:
            break

    if start is None:
        print("Error: Starting position S not found.")
        return

    # State: row, column, collected keys.
    start_state = (start[0], start[1], 0)

    # Queue stores (state, distance).
    queue = deque([(start_state, 0)])

    # Remember explored states.
    visited = {start_state}

    # Remember how each state was reached.
    parent = {start_state: None}

    # Up, down, left, right.
    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]

    end_state = None

    while queue:

        (r, c, keys), distance = queue.popleft()

        # Check whether the exit is reached.
        if maze[r][c] == 'E':
            end_state = (r, c, keys)
            print("Shortest distance:", distance)
            break

        # Explore neighboring cells.
        for dr, dc in directions:

            nr = r + dr
            nc = c + dc

            # Check maze boundaries.
            if not (0 <= nr < ROWS and 0 <= nc < COLS):
                continue

            cell = maze[nr][nc]

            # Cannot enter a wall.
            if cell == '#':
                continue

            # A door requires its matching key.
            # E is the exit, not a door.
            if cell != 'E' and 'A' <= cell <= 'F':

                required_key = key_bit(cell)

                # Skip the door if its key is missing.
                if not (keys & required_key):
                    continue

            # Collect a key when entering its cell.
            new_keys = keys

            if 'a' <= cell <= 'f':
                new_keys = keys | key_bit(cell)

            # Include the key inventory in the state.
            new_state = (nr, nc, new_keys)

            # Explore each state only once.
            if new_state not in visited:

                visited.add(new_state)

                parent[new_state] = (r, c, keys)

                queue.append(
                    (new_state, distance + 1)
                )

    # No valid route was found.
    if end_state is None:
        print("Shortest distance: -1")
        print("No valid path exists.")
        return

    # -------------------------------
    # 5. RECONSTRUCT THE SHORTEST PATH
    # -------------------------------

    path = []
    state = end_state

    while state is not None:

        path.append((state[0], state[1]))

        state = parent[state]

    path.reverse()

    print("Path length:", len(path) - 1)
    print("Path coordinates:", path)

    # -------------------------------
    # 6. DISPLAY THE COLORED MAZE
    # -------------------------------

    visualize_maze(path)

    # -------------------------------
    # 7. EXPORT THE PATH TO CSV
    # -------------------------------

    result = [row[:] for row in maze]

    for r, c in path:

        cell = maze[r][c]

        # Preserve the original symbol on path cells.
        if cell in 'Sa-fA-FE':
            result[r][c] = 'x' + cell
        else:
            result[r][c] = 'x'

    with open("path_grid.csv", "w", newline="") as file:

        writer = csv.writer(file)
        writer.writerows(result)

    print("Path saved to path_grid.csv")

    print("\nMaze with shortest path:")

    for row in result:
        print(" ".join(row))


# -------------------------------
# 8. RUN THE PROGRAM
# -------------------------------

if __name__ == "__main__":
    solve_maze()
