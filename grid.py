import pynput._util.win32
from pynput.mouse import Listener as mouseListener
import pyhk_pynput as pyhk
import subprocess
import config
import ctypes
from ctypes.wintypes import POINT, RECT
from functions import user32
from functions import print_handles, is_aero_enabled
from functions import get_actual_rect, to_rect

id4 = None
proc = None
hwnd = None


def find_matching_grid(mx, my):
    for grid in config.GRID:
        grid = list(map(int, grid))
        rect = to_rect(grid)
        if mx >= rect.left and mx <= rect.right and my >= rect.top and my <= rect.bottom:
            return grid
    return None


def action_handler():
    print("mouse")
    global id4, proc, hwnd
    if proc is None:
        proc = subprocess.Popen(["python", "overlay.py"])
    mouse = POINT()
    user32.GetCursorPos(ctypes.byref(mouse))
    hwnd = user32.WindowFromPoint(mouse)
    id4 = hot.addHotkey(['mouse middle'], up, isThread=False, up=True)


def up():
    global id4, proc, hwnd
    mouse = POINT()
    user32.GetCursorPos(ctypes.byref(mouse))

    hot.removeHotkey(id=id4)

    if proc is not None:
        proc.terminate()

    print("-" * 40)
    print_handles("GetForegroundWindow", user32.GetForegroundWindow())
    active_window = print_handles("WindowFromPoint", hwnd)
    print_handles("GetParent", user32.GetParent(active_window))
    ancestor = print_handles(
        "GetAncestor", user32.GetAncestor(active_window, 3))

    if ancestor:
        # GetAncestor is the most correct for our use-case, so prefer it.
        active_window = ancestor

    rect = RECT()
    user32.GetWindowRect(active_window, ctypes.byref(rect))
    grid = find_matching_grid(mouse.x, mouse.y)

    if grid:
        grid = to_rect(grid)
        if is_aero_enabled():
            arect = get_actual_rect(active_window)
            grid.left -= abs(arect.left - rect.left)
            grid.top -= abs(arect.top - rect.top)
            grid.right += abs(arect.right - rect.right)
            grid.bottom += abs(arect.bottom - rect.bottom)

        width = grid.right - grid.left
        height = grid.bottom - grid.top

        print("width: %d height: %d" % (width, height))

        HWND_NOTOPMOST = -2
        user32.SetWindowPos(active_window, HWND_NOTOPMOST,
                            grid.left, grid.top, width, height, 0)

        user32.SetForegroundWindow(active_window)

    proc = None
    hwnd = None


def call_next_hook_ex(hook, code, msg, lpdata):
    """ Allow mouse to not propagate """
    global hot
    for (hk, fun) in hot.UserHKF:
        if hot.isHotkey(hk):
            return msg in (mouseListener._WM_MBUTTONDOWN, mouseListener._WM_MBUTTONUP)
    return 0

pynput._util.win32.SystemHook._CallNextHookEx = staticmethod(call_next_hook_ex)

hot = pyhk.pyhk()
hot.addHotkey(['Ctrl', 'Alt', 'mouse middle'],
              action_handler, isThread=False)
hot.start()
