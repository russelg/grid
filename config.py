import math
from functions import get_dimensions, pad_grid_simple, pad_monitors
from functools import partial


def spiral(monitor, squares=5):
    x1, y1, x2, y2 = monitor
    wa = get_dimensions(monitor)
    _cls = list(range(1, squares + 1))
    n = len(_cls)
    old_width, old_height = wa.width, 2 * wa.height

    to_send = []

    for k in _cls:
        if k % 2 == 0:
            wa.width, old_width = math.ceil(old_width / 2), wa.width
            if k is not n:
                wa.height, old_height = math.floor(
                    wa.height / 2), wa.height
        else:
            wa.height, old_height = math.ceil(old_height / 2), wa.height
            if k is not n:
                wa.width, old_width = math.floor(
                    wa.width / 2), wa.width

        if k % 4 is 0:
            wa.x -= wa.width
        elif k % 2 is 0:
            wa.x += old_width
        elif k % 4 is 3 and k < n:
            wa.x += math.ceil(old_width / 2)

        if k % 4 is 1 and k is not 1:
            wa.y -= wa.height
        elif k % 2 is 1 and k is not 1:
            wa.y += old_height
        elif k % 4 is 0 and k < n:
            wa.y += math.ceil(old_height / 2)

        g = {
            "x": int(wa.x),
            "y": int(wa.y),
            "width": int(wa.width),
            "height": int(wa.height)
        }
        to_send.append(
            [g["x"], g["y"], g["x"] + g["width"], g["y"] + g["height"]])

    return to_send


def one_main_two_side(monitor, split=300):
    x1, y1, x2, y2 = monitor
    wa = get_dimensions(monitor)

    grid = []

    second_half = x1 + (wa.width / 2) + split
    grid.append([x1, y1, second_half, y2])

    screen_y_split = (y2 - y1) / 2
    grid.append([second_half, y1, x2, screen_y_split])
    grid.append([second_half, screen_y_split, x2, y2])

    return grid


def two_mains(monitor):
    x1, y1, x2, y2 = monitor
    wa = get_dimensions(monitor)
    split = 0

    grid = []

    second_half = x1 + (wa.width / 2) + split
    grid.append([x1, y1, second_half, y2])
    grid.append([second_half, y1, x2, y2])

    return grid


def two_mains_vertical(monitor):
    x1, y1, x2, y2 = monitor
    wa = get_dimensions(monitor)
    split = 0

    grid = []

    second_half = y1 + (wa.height / 2) + split
    grid.append([x1, y1, x2, second_half])
    grid.append([x1, second_half, x2, y2])
    grid.append([x1, y1, x2, y2])

    return grid


def two_mains_two_sides(monitor):
    x1, y1, x2, y2 = monitor
    wa = get_dimensions(monitor)

    grid = []

    thirds = wa.width / 3

    grid.append([x1, y1, x1 + thirds, y2])

    screen_y_split = (y2 - y1) / 2
    grid.append([x1 + thirds, y1, x1 + (thirds * 2), screen_y_split])
    grid.append([x1 + thirds, screen_y_split, x1 + (thirds * 2), y2])

    grid.append([x1 + (thirds * 2), y1, x2, y2])

    return grid


def two_mains_two_splits_two_sides(monitor):
    x1, y1, x2, y2 = monitor
    wa = get_dimensions(monitor)
    # split = 300

    grid = []

    thirds = wa.width / 3
    grid.append([x1, y1, x1 + thirds, y2])

    screen_y_split = (y2 - y1) / 2

    grid.append([x1 + thirds, y1, x1 + (thirds * 2), screen_y_split])
    grid.append([x1 + thirds, screen_y_split, x1 + (thirds * 2), y2])

    grid.append([x1 + (thirds * 2), y1, x2, screen_y_split])
    grid.append([x1 + (thirds * 2), screen_y_split, x2, y2])

    return grid

PADDING = 20
# 2d list of the dimensions of your monitors
Monitors = [
    [-1080, -469 + 24, 0, 1451],
    [0, 0 + 24, 1920, 1080],
    [1920, 0 + 26, 3840, 1080]
]

# save some typing by setting a default padding value
padded = partial(pad_grid_simple, padding=PADDING)

# pad monitor borders as well
Monitors = pad_monitors(padded, Monitors, padding=PADDING)

GRID = padded(two_mains_vertical(monitor=Monitors[0]))
GRID += pad_grid_simple(one_main_two_side(
    monitor=Monitors[1], split=100), padding=9)
GRID += padded(two_mains_two_sides(monitor=Monitors[2]))
# GRID += two_mains_two_sides(monitor=Monitors[2])
