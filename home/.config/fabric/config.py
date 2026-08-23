#!/home/siduck/.config/fabric/venv/bin/python
"""
Dock, ported from ~/.config/eww.

Layout and styling are unchanged. What changed is how the data gets in:
nothing here polls X. scripts/taskbar.sh (a `while true` with no sleep running
`xprop -root` every iteration) is replaced by one X connection on the GLib main
loop, and the icon cache built by gen_icons.sh is replaced by Gio's desktop app
database. What's left on a timer is two things: system readings every 2s and a
package-update check every ~15min.
"""

import os
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib

from fabric import Application
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.datetime import DateTime
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.x11 import X11Window
from fabric.system_tray.widgets import SystemTray
from fabric.utils import get_relative_path, monitor_file

from modules import misc, sysinfo, theme
from modules.dock import Dock
from modules.strut import reserve_bottom
from modules.volume import VolumeSlider
from modules.workspaces import Workspaces
from modules.xevents import X11Service

WIDTH_RATIO = 0.90
STRUT = 63


class DockWindow(X11Window):
    def __init__(self, x11, **kwargs):
        monitor = Gdk.Display.get_default().get_primary_monitor().get_geometry()
        width = int(monitor.width * WIDTH_RATIO)

        self.readings = sysinfo.Readings()

        left = Box(
            v_align="center",
            space_evenly=False,
            children=[
                misc.distro_icon(),
                Workspaces(x11),
                Dock(x11),
            ],
        )

        middle = Box(
            v_align="center",
            h_align="end",
            space_evenly=False,
            children=DateTime(
                formatters="%a %e | %H:%M",
                interval=1000,
                style_classes=["txt", "datetime"],
            ),
        )

        right = Box(
            v_align="center",
            h_align="end",
            space_evenly=False,
            spacing=9,
            style_classes=["right", "modal"],
            children=[
                misc.PackageUpdates(),
                misc.theme_switcher(),
                sysinfo.temperature(self.readings),
                sysinfo.battery(self.readings),
                sysinfo.ram(self.readings),
                sysinfo.cpu(self.readings),
                VolumeSlider(),
                misc.WifiIcon(),
                misc.power_button(),
                SystemTray(icon_size=24, spacing=3, style_classes="tray"),
            ],
        )

        super().__init__(
            title="Fabric - dock",  # the rofi helper scripts search for this name
            type_hint="dock",
            geometry="bottom",
            layer="top",
            margin="0px 0px 4px 0px",
            size=(width, -1),
            child=CenterBox(
                style_classes="zuup",
                start_children=left,
                center_children=middle,
                end_children=right,
            ),
            all_visible=True,
            **kwargs,
        )

        # X11Window has no exclusivity/reserve of its own, so the strut that
        # openbox reads has to be set by hand once the window is realized
        self.connect("size-allocate", lambda *_: reserve_bottom(self, STRUT))


def trim_memory():
    """
    Hand the arenas back after startup.

    Building the widget tree and the icon manifest churns a lot of short-lived
    objects; glibc holds onto those arenas by default. gc.freeze also moves
    everything alive at this point out of the collector's reach, so the
    generational passes stay small for the rest of the process's life.
    """
    import gc
    import ctypes

    gc.collect()
    gc.freeze()
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except (OSError, AttributeError):
        pass
    return False


def apply_style(app):
    app.set_stylesheet_from_string(
        theme.compile_stylesheet(get_relative_path("./style.css")),
        compile=False,
    )


if __name__ == "__main__":
    x11 = X11Service()
    window = DockWindow(x11)

    app = Application("dock", window)
    apply_style(app)

    # set_theme rewrites ~/.config/theme; restyle live instead of restarting
    monitor_file(theme.THEME_FILE, lambda *_: apply_style(app))

    # once the tree is realized and the first frame is out
    GLib.timeout_add(3000, trim_memory)

    app.run()
