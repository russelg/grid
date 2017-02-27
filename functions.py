import ctypes
import ctypes.wintypes
from recordclass import recordclass
from ctypes.wintypes import HWND, RECT, DWORD

user32 = ctypes.WinDLL("user32")
dwmapi = ctypes.WinDLL("dwmapi")

user32.SetWindowPos.restype = ctypes.wintypes.BOOL
user32.SetWindowPos.argtypes = (
    ctypes.wintypes.HWND,  # hWnd
    ctypes.wintypes.HWND,  # hWndInsertAfter
    ctypes.c_int,  # X
    ctypes.c_int,  # Y
    ctypes.c_int,  # cx
    ctypes.c_int,  # cy
    ctypes.c_uint)  # uFlags

Dimensions = recordclass('Dimensions', 'x y width height')


def get_class_name(hwnd):
    """Gets the class identifier of a window handle

    Retrieves the name of the class to which the specified window belongs.

    Args:
        hwnd: A handle to the window and, indirectly, the class to which the
            window belongs.

    Returns:
        The class name string.

        If the user32 call fails, it will return None.
    """
    MAX_LENGTH = 1024

    buff = ctypes.create_unicode_buffer(MAX_LENGTH)
    retval = user32.GetClassNameW(hwnd, buff, len(buff))
    if retval == 0:
        return None
    return buff.value


def print_handles(name, hwnd):
    """Prints window handle data

    Prints nicely formatted info regarding a window handle
    Args:
        name: An identifier to label this data with.
        hwnd: A handle to the window.

    Returns:
        Prints like so:

        GetAncestor: 66504 / 0x103c8 | Class: Chrome_WidgetWin_1
    """
    formatted = {
        "name": name,
        "hwnd": hwnd,
        "hex": hex(hwnd),
        "cls": get_class_name(hwnd)
    }
    print('\t{name}: {hwnd} / {hex} | Class: {cls}'.format(**formatted))
    return hwnd


def is_aero_enabled():
    """Checks if DWM composition is enabled

    Obtains a value that indicates whether Desktop Window Manager (DWM) composition is enabled

    Returns:
        True if DWM composition is enabled; otherwise, False.
    """
    try:
        c_bool = ctypes.c_bool()
        retcode = dwmapi.DwmIsCompositionEnabled(ctypes.byref(c_bool))
        return (retcode == 0 and c_bool.value)
    except AttributeError:
        # No windll, no dwmapi or no DwmIsCompositionEnabled function.
        return False


def to_rect(coords):
    """Converts a set of coordinates to a windows RECT

    Converts the form [x1, y1, x2, y2] to a windows RECT structure.

    Args:
        coords: List of coordinates in the form [x1, y1, x2, y2].

    Returns:
        A windows RECT structure.
    """
    rect = ctypes.wintypes.RECT(*coords)
    return rect


def get_dimensions(coords):
    """Converts a set of coordinates to Dimensions (recordclass)

    Converts the form [x1, y1, x2, y2] to a recordclass with:
        x, y, width, height.

    Args:
        coords: List of coordinates in the form [x1, y1, x2, y2].

    Returns:
        Named tuple with (x, y, width, height).

        Given [0, 26, 1920, 1080], returns:
        Dimensions(x=0, y=26, width=1920, height=1054)
    """
    x1, y1, x2, y2 = coords
    return Dimensions(x=x1, y=y1, width=(x2 - x1), height=(y2 - y1))


def get_actual_rect(hwnd):
    """Gets correct dimensions of a DWM controlled window

    "Retrieves the extended frame bounds rectangle in screen space".
    Windows 10 reports (technically) incorrect window dimensions,
    so this is used to obtain the correct window dimensions.

    Args:
        hwnd: The handle to the window from which the attribute data is retrieved.

    Returns:
        A windows RECT structure of the correct window dimensions.
    """
    rect = RECT()
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    dwmapi.DwmGetWindowAttribute(HWND(hwnd),
                                 DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
                                 ctypes.byref(rect),
                                 ctypes.sizeof(rect))
    # actual_x1 = rect.left
    # actual_y1 = rect.top
    # actual_x2 = rect.right
    # actual_y2 = rect.bottom
    # return [actual_x1, actual_y1, actual_x2, actual_y2]
    return rect


def pad_monitors(func, monitors, padding=20):
    for idx, monitor in enumerate(monitors):
        monitors[idx] = func(monitor, padding=int(padding / 2))

    return monitors


def pad_grid(grid, padding=20):
    """[Deprecated] Adds padding to a grid

    Adds padding (spacing between grid items) to a predefined grid.

    Args:
        grid: A list of lists of coordinates ([x1, y1, x2, y2]).
        padding: The padding between grid items in pixels (default: 40px)

    Returns:
        A new grid with padding applied to all applicable items.
    """

    original_grid = grid[:]
    def pad(coords):
        coords = list(map(int, coords))
        rect = to_rect(coords)

        adjacent = set([])
        modify_rect = to_rect(coords)
        for entry in original_grid:
            lrect = to_rect(list(map(int, entry)))

            if rect.right == lrect.left:
                adjacent.add('left')

            if rect.left == lrect.right:
                adjacent.add('right')

            if rect.bottom == lrect.top:
                if 'bottom' not in adjacent:
                    modify_rect.bottom += int(padding / 2)
                adjacent.add('bottom')

            if rect.top == lrect.bottom:
                if 'top' not in adjacent:
                    modify_rect.top -= int(padding / 2)
                adjacent.add('top')

        rect = modify_rect
        to_pad = set([])
        adjacent.add('left')

        if 'top' in adjacent:
            to_pad |= set(['top'])
        if 'left' in adjacent:
            to_pad |= set(['right'])
        if 'bottom' in adjacent:
            to_pad |= set(['bottom'])

        if adjacent == set(['right', 'left']):
            to_pad |= set(['right'])
            to_pad -= set(['left'])

        for d in to_pad:
            val = getattr(rect, d)
            if d is 'left' or d is 'top':
                setattr(rect, d, val + padding)
            elif d is 'right' or d is 'bottom':
                setattr(rect, d, val - padding)

        return [rect.left, rect.top, rect.right, rect.bottom]

    if not all((isinstance(x, list) for x in grid)):
        # if only one grid is provided, handle that case
        # useful if you want to pad the monitor borders as well
        return pad(grid)

    for idx, coords in enumerate(grid):
        grid[idx] = pad(coords)

    return grid


def pad_grid_simple(grid, padding=20):
    """Adds padding to a grid

    Adds padding (spacing between grid items) to a predefined grid.

    Args:
        grid: A list of lists of coordinates ([x1, y1, x2, y2]).
        padding: The padding between grid items in pixels (default: 40px)

    Returns:
        A new grid with padding applied to all applicable items.
    """

    def pad(coords):
        coords = list(map(int, coords))
        rect = to_rect(coords)

        rect.left += padding
        rect.top += padding
        rect.right -= (padding)
        rect.bottom -= (padding)
        return [rect.left, rect.top, rect.right, rect.bottom]

    if not all((isinstance(x, list) for x in grid)):
        # if only one grid is provided, handle that case
        # useful if you want to pad the monitor borders as well
        return pad(grid)

    for idx, coords in enumerate(grid):
        grid[idx] = pad(coords)

    return grid
