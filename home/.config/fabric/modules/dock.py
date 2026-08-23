"""
Taskbar + pinned apps.

Icons come from Gio's desktop app database, so gen_icons.sh and the old
cache/icons file are gone -- no grepping every .desktop, and StartupWMClass is
honoured properly instead of guessed at.
"""

import os
import gi
import json

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk, GdkPixbuf, GLib

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.revealer import Revealer
from fabric.utils import get_desktop_applications, exec_shell_command_async, monitor_file

PINNED_FILE = os.path.expanduser("~/.config/fabric/pinned_apps.json")
CACHE_DIR = os.path.expanduser("~/.config/fabric/cache")
MANIFEST = os.path.join(CACHE_DIR, "icons.json")
BLOB = os.path.join(CACHE_DIR, "icons.bin")

APP_DIRS = (
    "/usr/share/applications",
    "/usr/local/share/applications",
    os.path.expanduser("~/.local/share/applications"),
)

# 32, not 30. Papirus ships per-size SVGs drawn on a fixed pixel grid, so a
# 32x32 icon squeezed into 30px loses its grid alignment and every edge goes
# soft. Rendering on the icon's own native grid is what keeps it crisp.
ICON_SIZE = 32


def pointer_x():
    """replaces `xdotool getmouselocation` for the popup scripts"""
    pointer = Gdk.Display.get_default().get_default_seat().get_pointer()
    return pointer.get_position()[1] if pointer else 0


def sanitize(name):
    """same key eww used: lowercased, spaces/dashes/dots folded to underscore"""
    return (name or "").translate(str.maketrans(" -.", "___")).lower()


class IconCache:
    """
    Rasterised icons, stored as raw RGBA in one flat file.

    Rendering a single Papirus SVG pulls librsvg into the process and costs
    8.6 MB -- more than every pixbuf we load put together. Rendering happens
    once, here; warm starts wrap the stored bytes with new_from_bytes, which
    loads no image loader at all. Not librsvg, not even the PNG one.
    """

    def __init__(self):
        self._blob = None

    @staticmethod
    def render(app, target=ICON_SIZE):
        """rasterise on the icon's native grid, so nothing has to be rescaled"""
        theme = Gtk.IconTheme.get_default()
        size = target

        if app.icon_name:
            # a -1 entry means genuinely scalable, so any size renders clean.
            # otherwise snap to the nearest native size at or above the target.
            sizes = [s for s in theme.get_icon_sizes(app.icon_name) if s > 0]
            if sizes and target not in sizes:
                above = [s for s in sizes if s >= target]
                size = min(above) if above else max(sizes)

        pixbuf = app.get_icon_pixbuf(size, default_icon=None)
        if pixbuf is None:
            return None
        # only ever scale down from a bigger grid, never up from a smaller one
        if pixbuf.get_width() != target:
            pixbuf = pixbuf.scale_simple(target, target, GdkPixbuf.InterpType.HYPER)
        return pixbuf

    def store(self, pixbuf):
        """append the pixels, return the descriptor to record in the manifest"""
        data = pixbuf.get_pixels()
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(BLOB, "ab") as f:
            offset = f.tell()
            f.write(data)
        return {
            "at": offset,
            "len": len(data),
            "w": pixbuf.get_width(),
            "h": pixbuf.get_height(),
            "stride": pixbuf.get_rowstride(),
            "alpha": pixbuf.get_has_alpha(),
        }

    def load(self, desc):
        if not desc:
            return None
        try:
            if self._blob is None:
                with open(BLOB, "rb") as f:
                    self._blob = f.read()
            raw = self._blob[desc["at"] : desc["at"] + desc["len"]]
            return GdkPixbuf.Pixbuf.new_from_bytes(
                GLib.Bytes.new(raw),
                GdkPixbuf.Colorspace.RGB,
                desc["alpha"],
                8,
                desc["w"],
                desc["h"],
                desc["stride"],
            )
        except (OSError, KeyError, TypeError):
            return None

    def reset(self):
        self._blob = None
        try:
            os.remove(BLOB)
        except OSError:
            pass


class AppIndex:
    """
    wm_class -> icon descriptor + launch command.

    Only plain data is kept; the Gio DesktopAppInfo objects are dropped once
    the manifest is built.
    """

    def __init__(self, on_changed=None):
        self.cache = IconCache()
        self._icons = {}
        self._cmds = {}
        self._on_changed = None
        self.load()
        self._on_changed = on_changed

        self._monitors = [
            monitor_file(d, lambda *_: self.rebuild())
            for d in APP_DIRS
            if os.path.isdir(d)
        ]

    def _stamp(self):
        return [int(os.stat(d).st_mtime) if os.path.isdir(d) else 0 for d in APP_DIRS]

    def load(self):
        """use the cached manifest while the .desktop dirs haven't changed"""
        try:
            with open(MANIFEST) as f:
                data = json.load(f)
            if data.get("stamp") == self._stamp() and data.get("size") == ICON_SIZE:
                self._icons = data["icons"]
                self._cmds = data["cmds"]
                return
        except (OSError, ValueError, KeyError):
            pass
        self.rebuild()

    def rebuild(self, *_):
        """re-render the icon cache -- the only path that ever touches librsvg"""
        self.cache.reset()
        self._icons = {}
        self._cmds = {}

        for app in get_desktop_applications():
            keys = [sanitize(k) for k in (app.window_class, app.name, app.executable)]
            if app.command_line:
                keys.append(sanitize(os.path.basename(app.command_line.split()[0])))
            keys = [k for k in keys if k]
            if not keys:
                continue

            pixbuf = IconCache.render(app)
            if pixbuf is None:
                continue
            desc = self.cache.store(pixbuf)

            for key in keys:
                self._icons.setdefault(key, desc)
                if app.executable:
                    self._cmds.setdefault(key, app.executable)

        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(MANIFEST, "w") as f:
                json.dump(
                    {
                        "stamp": self._stamp(),
                        "size": ICON_SIZE,
                        "icons": self._icons,
                        "cmds": self._cmds,
                    },
                    f,
                )
        except OSError:
            pass

        self._on_changed() if self._on_changed else None

    def _find(self, table, wm_class):
        key = sanitize(wm_class)
        if key in table:
            return table[key]
        for candidate, value in table.items():
            if candidate.startswith(key) or key.startswith(candidate):
                return value
        return None

    def icon(self, wm_class):
        return self.cache.load(self._find(self._icons, wm_class))

    def command(self, wm_class):
        return self._find(self._cmds, wm_class)


class TaskIcon(Box):
    def __init__(self, dock, entry, **kwargs):
        super().__init__(space_evenly=False, **kwargs)
        self.dock = dock
        self.entry = entry

        self.pin_button = Button(
            label="Unpin ?" if entry["pinned"] and not entry["ids"] else "  Pin App",
            style_classes=["pinbtn", "txt"],
            on_clicked=self.on_pin,
        )
        self.revealer = Revealer(
            child=self.pin_button,
            transition_type="slide-right",
            child_revealed=dock.clicked == entry["key"],
        )

        image = Image()
        if entry["icon"] is not None:
            image.set_from_pixbuf(entry["icon"])

        self.button = Button(
            child=image,
            style_classes=["taskicon", f"taskicon_{entry['state']}"],
            on_clicked=self.on_click,
            on_button_press_event=self.on_button_press,
        )

        self.children = [self.button, self.revealer]

    def on_button_press(self, _, event):
        if event.button == 3:
            self.dock.toggle_pin_prompt(self.entry["key"])
            return True
        return False

    def on_click(self, *_):
        ids = self.entry["ids"]

        if not ids:  # pinned, not running
            cmd = self.entry.get("cmd") or self.dock.index.command(self.entry["key"])
            exec_shell_command_async(cmd) if cmd else None
            return

        if len(ids) == 1:
            wid = ids[0]
            if self.entry["state"] == "focused":
                self.dock.x11.minimize(wid)
            else:
                self.dock.x11.activate(wid)
            return

        # more than one window of this class: pick one
        from modules.popup import Picker

        x11 = self.dock.x11
        Picker(
            items=[(x11.get_wm_name(i) or f"window {i}", i) for i in ids],
            on_select=lambda wid: x11.activate(wid),
            at_x=pointer_x(),
            dock_height=self.dock.get_toplevel().get_allocated_height(),
            title="Window",
        )

    def on_pin(self, *_):
        if self.entry["pinned"] and not self.entry["ids"]:
            self.dock.unpin(self.entry["key"])
        else:
            self.dock.pin(self.entry)


class Dock(Box):
    def __init__(self, x11, **kwargs):
        super().__init__(
            style_classes="taskbar",
            h_align="end",
            space_evenly=False,
            spacing=5,
            **kwargs,
        )
        self.x11 = x11
        self.clicked = None
        self.pinned = self.load_pinned()
        self.index = AppIndex()
        self.index._on_changed = self.render

        x11.clients_changed.connect(self.render)
        x11.active_changed.connect(self.render)

        self.render()

    # -- pinned apps ------------------------------------------------------

    def load_pinned(self):
        try:
            with open(PINNED_FILE) as f:
                return json.load(f)
        except (OSError, ValueError):
            return []

    def save_pinned(self):
        with open(PINNED_FILE, "w") as f:
            json.dump(self.pinned, f, indent=2)

    def pin(self, entry):
        if any(p["name"] == entry["key"] for p in self.pinned):
            return self.toggle_pin_prompt(None)

        cmd = entry.get("cmd")
        if not cmd and entry["ids"]:
            pid = self.x11.get_pid(entry["ids"][0])
            if pid:
                try:
                    cmd = os.readlink(f"/proc/{pid}/exe")
                except OSError:
                    cmd = None

        self.pinned.append(
            {"name": entry["key"], "cmd": cmd or self.index.command(entry["key"]) or ""}
        )
        self.save_pinned()
        self.clicked = None
        self.render()

    def unpin(self, key):
        self.pinned = [p for p in self.pinned if p["name"] != key]
        self.save_pinned()
        self.clicked = None
        self.render()

    def toggle_pin_prompt(self, key):
        self.clicked = None if self.clicked == key else key
        self.render()

    # -- rendering --------------------------------------------------------

    def collect(self):
        """group open windows by wm_class, then fold in pinned apps not running"""
        groups = {}
        active = self.x11.active

        for wid in self.x11.clients:
            wm_class = self.x11.get_wm_class(wid)
            if not wm_class:
                continue
            key = sanitize(wm_class)
            groups.setdefault(key, {"key": key, "ids": [], "class": wm_class})
            groups[key]["ids"].append(wid)

        entries = []
        for key, group in groups.items():
            ids = group["ids"]
            if active in ids:
                state = "focused"
            elif all(self.x11.is_hidden(i) for i in ids):
                state = "minimized"
            else:
                state = "unfocused"
            entries.append(
                {
                    "key": key,
                    "ids": ids,
                    "icon": self.index.icon(group["class"]),
                    "state": state,
                    "pinned": any(p["name"] == key for p in self.pinned),
                    "cmd": None,
                }
            )

        for pin in self.pinned:
            if pin["name"] in groups:
                continue
            entries.append(
                {
                    "key": pin["name"],
                    "ids": [],
                    "icon": self.index.icon(pin["name"]),
                    "state": "unfocused",
                    "pinned": True,
                    "cmd": pin.get("cmd"),
                }
            )

        # pinned first, in file order, so icons don't jump around
        order = [p["name"] for p in self.pinned]
        entries.sort(
            key=lambda e: (
                order.index(e["key"]) if e["key"] in order else len(order),
                e["key"],
            )
        )
        return entries

    def render(self, *_):
        for child in self.children:
            child.destroy()
        self.children = [TaskIcon(self, entry) for entry in self.collect()]
        self.show_all()
