"""
X11Window does not reserve space -- it never sets _NET_WM_STRUT_PARTIAL.
This is the equivalent of eww's `:reserve (struts :side "bottom" ...)`.

openbox honours the strut and its x-range, so the space is reserved on the
monitor the dock sits on. dwm ignores struts entirely; there the gap still
comes from extbarheight, so this is a harmless no-op.
"""

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk


def reserve_bottom(window, distance):
    """reserve `distance` px along the bottom edge, limited to the dock's x-range"""
    gdk_window = window.get_window()
    if gdk_window is None:
        return False

    try:
        from Xlib.display import Display
    except ImportError:
        return False

    display = Display()
    xwindow = display.create_resource_object("window", gdk_window.get_xid())

    gdk_display = Gdk.Display.get_default()
    monitor = gdk_display.get_primary_monitor().get_geometry()
    screen = Gdk.Screen.get_default()
    screen_height = screen.get_height()

    x, _ = window.get_position()
    width = window.get_allocated_width()

    # struts are measured from the edge of the whole X screen, not the monitor,
    # so anything below this monitor has to be added on
    below = screen_height - (monitor.y + monitor.height)

    # left, right, top, bottom,
    # left_start_y, left_end_y, right_start_y, right_end_y,
    # top_start_x, top_end_x, bottom_start_x, bottom_end_x
    strut = [0, 0, 0, below + distance, 0, 0, 0, 0, 0, 0, x, x + width - 1]

    partial = display.intern_atom("_NET_WM_STRUT_PARTIAL")
    plain = display.intern_atom("_NET_WM_STRUT")
    cardinal = display.intern_atom("CARDINAL")

    xwindow.change_property(partial, cardinal, 32, strut)
    xwindow.change_property(plain, cardinal, 32, strut[:4])
    display.sync()
    return True
