"""
Volume slider.

Same pactl the eww config used, but the level is no longer guessed at: the
slider now starts at the real volume and follows changes made elsewhere,
because `pactl subscribe` streams sink events instead of us polling for them.
Avoids fabric's Audio service, which needs libcvc compiled.
"""

import re

from fabric.widgets.box import Box
from fabric.widgets.scale import Scale
from fabric.widgets.button import Button
from fabric.widgets.revealer import Revealer
from fabric.utils import exec_shell_command_async, cooldown

_VOLUME_RE = re.compile(r"(\d+)%")


class VolumeSlider(Box):
    def __init__(self, **kwargs):
        super().__init__(
            style_classes="volume-slider", space_evenly=False, **kwargs
        )

        self._syncing = False

        # connect after assignment: Scale fires value-changed while it is still
        # being constructed, before self.scale exists
        self.scale = Scale(
            min_value=0,
            max_value=100,
            value=50,
            digits=0,
            orientation="h",
        )
        self.scale.connect("value-changed", self.on_slide)
        self.revealer = Revealer(
            child=self.scale,
            transition_type="slide-right",
            child_revealed=True,
        )
        self.toggle_button = Button(
            label="\uf027",
            style_classes="theme_switcher",
            on_clicked=lambda *_: self.revealer.set_reveal_child(
                not self.revealer.get_reveal_child()
            ),
        )

        self.children = [self.toggle_button, self.revealer]

        self.refresh()
        # one long-lived subscriber process, woken by pulse, not by a timer
        exec_shell_command_async("pactl subscribe", self.on_pulse_event)

    def on_pulse_event(self, line):
        if "sink" in line:
            self.refresh()

    def refresh(self, *_):
        exec_shell_command_async(
            "pactl get-sink-volume @DEFAULT_SINK@", self.on_volume_read
        )

    def on_volume_read(self, line):
        match = _VOLUME_RE.search(line)
        if not match:
            return
        self._syncing = True
        self.scale.value = int(match.group(1))
        self._syncing = False

    @cooldown(0.05)
    def on_slide(self, *_):
        if self._syncing:
            return
        exec_shell_command_async(
            f"pactl set-sink-volume @DEFAULT_SINK@ {round(self.scale.value)}%"
        )
