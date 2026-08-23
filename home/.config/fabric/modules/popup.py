"""
Native picker popup -- replaces rofi_menu.sh and theme_switcher.sh.

Those two scripts spawned rofi (a whole second GUI process, ~120ms to first
paint) plus three xdotool calls just to find where the dock was. This is a GTK
window we already have the toolkit for: it opens instantly, costs nothing when
closed, and is styled from the same palette as everything else.
"""

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.x11 import X11Window
from fabric.widgets.entry import Entry
from fabric.widgets.scrolledwindow import ScrolledWindow

GAP = 8
WIDTH = 300
MAX_VISIBLE = 12


class Picker(X11Window):
    """a filterable list anchored just above the dock"""

    def __init__(self, items, on_select, at_x, dock_height, title="Search"):
        self._items = list(items)          # [(label, value), ...]
        self._on_select = on_select
        self._buttons = []

        self.entry = Entry(
            placeholder=title,
            name="picker-entry",
            on_changed=lambda e, *_: self.filter(e.get_text()),
            on_activate=lambda *_: self.activate_first(),
        )

        self.list_box = Box(orientation="v", spacing=2, name="picker-list")
        self.build()

        scroller = ScrolledWindow(
            child=self.list_box,
            h_scrollbar_policy="never",
            v_scrollbar_policy="automatic",
            propagate_width=True,
            propagate_height=True,
        )

        screen = Gdk.Display.get_default().get_primary_monitor().get_geometry()
        x = max(0, min(at_x - WIDTH // 2, screen.width - WIDTH))

        super().__init__(
            title="Fabric - picker",
            type_hint="menu",
            geometry="bottom-left",
            layer="top",
            # (top, right, bottom, left): right shifts x, bottom lifts it clear
            margin=(0, x, dock_height + GAP, 0),
            size=(WIDTH, -1),
            name="picker",
            child=Box(
                orientation="v",
                spacing=6,
                name="picker-inner",
                children=[self.entry, scroller],
            ),
            all_visible=True,
        )

        self.add_keybinding("escape", lambda *_: self.dismiss())
        self.connect("focus-out-event", lambda *_: self.dismiss())
        self.steal_input_soft()
        self.entry.grab_focus()

    def build(self, needle=""):
        for button in self._buttons:
            button.destroy()
        self._buttons = []

        needle = needle.casefold()
        shown = 0
        for label, value in self._items:
            if needle and needle not in label.casefold():
                continue
            if shown >= MAX_VISIBLE:
                break
            button = Button(
                child=Label(label=label, h_align="start", ellipsization="end"),
                style_classes="picker-item",
                on_clicked=lambda _, v=value: self.choose(v),
            )
            self._buttons.append(button)
            shown += 1

        self.list_box.children = self._buttons
        self.list_box.show_all()

    def filter(self, needle):
        self.build(needle)

    def activate_first(self):
        self._buttons[0].clicked() if self._buttons else self.dismiss()

    def choose(self, value):
        self.dismiss()
        self._on_select(value)

    def dismiss(self, *_):
        self.unsteal_input()
        self.destroy()
