
from collections import deque


def key_bit(letter):
    return 1 << (ord(letter.lower()) - ord('a'))


def shortest_distance(maze):
    rows = len(maze)
    cols = len(maze[0])

    start = None

    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == 'S':
                start = (r, c)
                break
        if start is not None:
            break

    if start is None:
        return -1

    # State: row, column, collected keys, distance
    queue = deque([(start[0], start[1], 0, 0)])
    visited = {(start[0], start[1], 0)}

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        r, c, keys, distance = queue.popleft()

        if maze[r][c] == 'E':
            return distance

        for dr, dc in directions:
            nr = r + dr
            nc = c + dc

            if not (0 <= nr < rows and 0 <= nc < cols):
                continue

            cell = maze[nr][nc]

            if cell == '#':
                continue

            # Doors A-F require matching keys a-f.
            # E represents the exit, not a door.
            if cell != 'E' and 'A' <= cell <= 'F':
                if not (keys & key_bit(cell)):
                    continue

            new_keys = keys

            # Collect keys automatically.
            if 'a' <= cell <= 'f':
                new_keys |= key_bit(cell)

            new_state = (nr, nc, new_keys)

            if new_state not in visited:
                visited.add(new_state)
                queue.append(
                    (nr, nc, new_keys, distance + 1)
                )

    return -1


# Test 1: Exit is blocked.
test_maze_1 = [
    list("S#E"),
    list("###"),
    list("...")
]

# Test 2: Door A blocks the only route; key a is absent.
test_maze_2 = [
    list("SAE"),
    list("###"),
    list("...")
]

tests = [
    ("Test 1: No valid path", test_maze_1, -1),
    ("Test 2: Door without its key", test_maze_2, -1)
]

for name, test_maze, expected in tests:
    result = shortest_distance(test_maze)

    print(f"\n{name}")
    print("Expected distance:", expected)
    print("Actual distance:", result)
    print("PASS" if result == expected else "FAIL")

# Test 3: Collect key a to pass through door A.
test_maze_3 = [
    list("SaAE")
]

expected = 3
result = shortest_distance(test_maze_3)

print("\nTest 3: Key required to reach exit")
print("Expected distance:", expected)
print("Actual distance:", result)
print("PASS" if result == expected else "FAIL")
