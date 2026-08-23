"""
One X11 connection, wired into the GLib main loop.

This is what replaces scripts/taskbar.sh. That script was a `while true` with
no sleep, running `xprop -root` every iteration -- thousands of forks a second,
forever. Here the X socket is watched by the main loop and nothing runs until
the server actually sends a PropertyNotify.
"""

import gi
from loguru import logger
from fabric.core.service import Service, Signal

gi.require_version("Gtk", "3.0")
from gi.repository import GLib

from Xlib import X, Xatom, display as xdisplay, error as xerror
from Xlib.protocol import event as xevent


class X11Service(Service):
    """root-window property watcher + the window actions the dock needs"""

    @Signal
    def clients_changed(self) -> None: ...

    @Signal
    def active_changed(self) -> None: ...

    @Signal
    def workspace_changed(self, index: int) -> None: ...

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.display = xdisplay.Display()
        self.root = self.display.screen().root

        self._atoms = {}
        self._watched = set()

        self.root.change_attributes(event_mask=X.PropertyChangeMask)
        self.display.sync()

        GLib.io_add_watch(
            self.display.fileno(), GLib.PRIORITY_DEFAULT, GLib.IO_IN, self._on_readable
        )

        self.clients = self.get_clients()
        self.active = self.get_active()
        self._watch_clients()

    # -- atoms ------------------------------------------------------------

    def atom(self, name):
        if name not in self._atoms:
            self._atoms[name] = self.display.intern_atom(name)
        return self._atoms[name]

    def _prop(self, window, name, kind=Xatom.CARDINAL):
        try:
            reply = window.get_full_property(self.atom(name), kind)
        except (xerror.BadWindow, xerror.XError):
            return None
        return reply.value if reply else None

    # -- event pump -------------------------------------------------------

    def _on_readable(self, *_):
        clients_dirty = active_dirty = False

        for _i in range(self.display.pending_events()):
            event = self.display.next_event()
            if event.type != X.PropertyNotify:
                continue

            name = self.display.get_atom_name(event.atom)

            if event.window.id == self.root.id:
                if name == "_NET_CLIENT_LIST":
                    clients_dirty = True
                elif name == "_NET_ACTIVE_WINDOW":
                    active_dirty = True
                elif name == "_NET_CURRENT_DESKTOP":
                    value = self._prop(self.root, "_NET_CURRENT_DESKTOP")
                    self.workspace_changed(int(value[0]) if value else 0)
            elif name in ("_NET_WM_STATE", "WM_NAME", "_NET_WM_NAME"):
                # minimize/restore, or a title change the rofi menu would show
                clients_dirty = True

        if clients_dirty:
            self.clients = self.get_clients()
            self.active = self.get_active()
            self._watch_clients()
            self.clients_changed()
        elif active_dirty:
            self.active = self.get_active()
            self.active_changed()

        return True

    def _watch_clients(self):
        """subscribe to state changes on new clients, so minimize is event-driven too"""
        for wid in self.clients:
            if wid in self._watched:
                continue
            try:
                self.display.create_resource_object("window", wid).change_attributes(
                    event_mask=X.PropertyChangeMask
                )
                self._watched.add(wid)
            except (xerror.BadWindow, xerror.XError):
                pass
        self._watched &= set(self.clients)
        self.display.flush()

    # -- reads ------------------------------------------------------------

    # window types that never belong on a taskbar -- without this the dock
    # lists itself, and any other bar/panel on screen
    _SKIP_TYPES = (
        "_NET_WM_WINDOW_TYPE_DOCK",
        "_NET_WM_WINDOW_TYPE_DESKTOP",
        "_NET_WM_WINDOW_TYPE_TOOLBAR",
        "_NET_WM_WINDOW_TYPE_MENU",
        "_NET_WM_WINDOW_TYPE_SPLASH",
        "_NET_WM_WINDOW_TYPE_NOTIFICATION",
    )

    def should_show(self, wid):
        window = self.window(wid)

        state = self._prop(window, "_NET_WM_STATE", Xatom.ATOM)
        if state and self.atom("_NET_WM_STATE_SKIP_TASKBAR") in list(state):
            return False

        types = self._prop(window, "_NET_WM_WINDOW_TYPE", Xatom.ATOM)
        if types:
            skip = {self.atom(t) for t in self._SKIP_TYPES}
            if skip & set(types):
                return False

        return True

    def get_clients(self):
        value = self._prop(self.root, "_NET_CLIENT_LIST", Xatom.WINDOW)
        if not value:
            return []
        return [wid for wid in value if self.should_show(wid)]

    def get_active(self):
        value = self._prop(self.root, "_NET_ACTIVE_WINDOW", Xatom.WINDOW)
        return value[0] if value else 0

    def get_workspace(self):
        value = self._prop(self.root, "_NET_CURRENT_DESKTOP")
        return int(value[0]) if value else 0

    def window(self, wid):
        return self.display.create_resource_object("window", wid)

    def get_wm_class(self, wid):
        try:
            pair = self.window(wid).get_wm_class()
        except (xerror.BadWindow, xerror.XError):
            return None
        # (instance, class) -- eww matched on the class half
        return pair[1] if pair and len(pair) > 1 else (pair[0] if pair else None)

    def get_wm_name(self, wid):
        window = self.window(wid)
        value = self._prop(window, "_NET_WM_NAME", self.atom("UTF8_STRING"))
        if value:
            return value if isinstance(value, str) else value.decode("utf-8", "replace")
        try:
            return window.get_wm_name() or ""
        except (xerror.BadWindow, xerror.XError):
            return ""

    def is_hidden(self, wid):
        value = self._prop(self.window(wid), "_NET_WM_STATE", Xatom.ATOM)
        if not value:
            return False
        hidden = self.atom("_NET_WM_STATE_HIDDEN")
        return hidden in list(value)

    def get_pid(self, wid):
        value = self._prop(self.window(wid), "_NET_WM_PID")
        return int(value[0]) if value else None

    # -- actions ----------------------------------------------------------

    def _send_root_message(self, wid, message, data=()):
        data = (list(data) + [0, 0, 0, 0, 0])[:5]
        self.root.send_event(
            xevent.ClientMessage(
                window=self.window(wid),
                client_type=self.atom(message),
                data=(32, data),
            ),
            event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask,
        )
        self.display.flush()

    def activate(self, wid):
        # source indication 2 = pager, which is what wms honour without a fight
        self._send_root_message(wid, "_NET_ACTIVE_WINDOW", [2, X.CurrentTime, 0])

    def minimize(self, wid):
        try:
            # IconicState -- let the wm do the iconifying, don't unmap behind its back
            self._send_root_message(wid, "WM_CHANGE_STATE", [3])
        except (xerror.BadWindow, xerror.XError) as e:
            logger.warning(f"[X11Service] could not minimize {wid}: {e}")

    def set_workspace(self, index):
        self.root.send_event(
            xevent.ClientMessage(
                window=self.root,
                client_type=self.atom("_NET_CURRENT_DESKTOP"),
                data=(32, [index, X.CurrentTime, 0, 0, 0]),
            ),
            event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask,
        )
        self.display.flush()
