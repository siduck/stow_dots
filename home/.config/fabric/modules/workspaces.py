"""
Workspace indicator.

eww polled this through `xprop -root -spy _NET_CURRENT_DESKTOP | while read`.
Now it hangs off the same X connection everything else uses.
"""

from fabric.widgets.box import Box
from fabric.widgets.button import Button

COUNT = 4
ACTIVE_GLYPH = "\U000f0ec2"
INACTIVE_GLYPH = "\uf444"


class Workspaces(Box):
    def __init__(self, x11, **kwargs):
        super().__init__(style_classes="workspaces", spacing=10, **kwargs)
        self.x11 = x11

        self.buttons = [
            Button(
                label=INACTIVE_GLYPH,
                on_clicked=lambda _, i=index: self.x11.set_workspace(i),
            )
            for index in range(COUNT)
        ]
        self.children = self.buttons

        x11.workspace_changed.connect(lambda _, index: self.sync(index))
        self.sync(x11.get_workspace())

    def sync(self, active):
        for index, button in enumerate(self.buttons):
            is_active = index == active
            button.set_label(ACTIVE_GLYPH if is_active else INACTIVE_GLYPH)
            button.remove_style_class("active_ws")
            button.remove_style_class("inactive_ws")
            button.add_style_class("active_ws" if is_active else "inactive_ws")
