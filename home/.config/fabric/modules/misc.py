"""
The small right-hand widgets: distro button, power, wifi, package updates,
theme switcher.
"""

import os
import gi

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.utils import exec_shell_command_async, invoke_repeater, monitor_file

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gio

WIFI_IFACE = "wlp194s0"


def distro_icon():
    return Button(
        label="\uf32e",
        style_classes="distroIcon",
        h_align="start",
        on_clicked=lambda *_: exec_shell_command_async(
            "eww -c /home/siduck/.config/chadwm/eww open eww"
        ),
    )


def power_button():
    return Button(
        label="\uf011",
        style_classes="powerBtn",
        on_clicked=lambda *_: exec_shell_command_async(
            "sh -c 'slock & loginctl suspend'"
        ),
    )


def theme_switcher():
    return Button(
        label="\U000f195a",
        style_classes="theme_switcher",
        on_clicked=_open_theme_picker,
    )


def _open_theme_picker(button, *_):
    from modules.popup import Picker
    from modules import theme

    names = sorted(f[:-5] for f in os.listdir(theme.THEMES_DIR) if f.endswith(".scss"))
    Picker(
        items=[(n, n) for n in names],
        on_select=lambda name: exec_shell_command_async(["set_theme", name]),
        at_x=_pointer_x(),
        dock_height=button.get_toplevel().get_allocated_height(),
        title="Theme",
    )


def _pointer_x():
    from gi.repository import Gdk

    pointer = Gdk.Display.get_default().get_default_seat().get_pointer()
    return pointer.get_position()[1] if pointer else 0


class WifiIcon(Box):
    """reads operstate instead of shelling out; NetworkMonitor wakes us on change"""

    def __init__(self, **kwargs):
        super().__init__(style_classes="wifiIcon", **kwargs)
        self._label = None

        from fabric.widgets.label import Label

        self._label = Label()
        self.children = self._label

        monitor = Gio.NetworkMonitor.get_default()
        monitor.connect("network-changed", lambda *_: self.sync())
        self.sync()

    def sync(self, *_):
        try:
            with open(f"/sys/class/net/{WIFI_IFACE}/operstate") as f:
                up = f.read().strip() == "up"
        except OSError:
            up = False
        self._label.set_label("\U000f0928" if up else "\U000f092d")


class PackageUpdates(Box):
    def __init__(self, interval=1000_000, **kwargs):
        super().__init__(style_classes=["txt", "pkgupdates"], **kwargs)

        from fabric.widgets.label import Label

        self._label = Label(label="\uf487  0")
        self.children = self._label

        self._count = 0
        invoke_repeater(interval, self.refresh)

    def refresh(self, *_):
        self._count = 0
        exec_shell_command_async(
            "sh -c 'doas xbps-install -un 2>/dev/null'", self.on_line
        )
        return True

    def on_line(self, line):
        if line.strip():
            self._count += 1
            self._label.set_label(f"\uf487  {self._count}")
