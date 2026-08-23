"""
cpu / ram / temp / battery, read straight from /proc and /sys.

eww's EWW_CPU / EWW_RAM / EWW_TEMPS / EWW_BATTERY magic vars did the same thing
internally; psutil would too, but it's another dependency for four file reads.
One 2s timer covers all four widgets.
"""

import os
import glob

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.utils import invoke_repeater


def _hwmon(name):
    for path in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            with open(os.path.join(path, "name")) as f:
                if f.read().strip() == name:
                    return path
        except OSError:
            continue
    return None


class Readings:
    """shared sampler -- one pass over /proc per tick, not one per widget"""

    def __init__(self, interval=2000):
        self._last_cpu = None
        self.cpu = self.ram = self.temp = self.battery = 0
        self._k10temp = _hwmon("k10temp")
        self._callbacks = []
        invoke_repeater(interval, self._tick)

    def subscribe(self, callback):
        self._callbacks.append(callback)
        callback()

    def _tick(self, *_):
        self.cpu = self._read_cpu()
        self.ram = self._read_ram()
        self.temp = self._read_temp()
        self.battery = self._read_battery()
        for callback in self._callbacks:
            callback()
        return True

    def _read_cpu(self):
        try:
            with open("/proc/stat") as f:
                fields = [int(v) for v in f.readline().split()[1:]]
        except (OSError, ValueError):
            return self.cpu

        idle = fields[3] + fields[4]
        total = sum(fields)

        if self._last_cpu is None:
            self._last_cpu = (idle, total)
            return 0

        idle_delta = idle - self._last_cpu[0]
        total_delta = total - self._last_cpu[1]
        self._last_cpu = (idle, total)

        if total_delta <= 0:
            return self.cpu
        return round(100 * (1 - idle_delta / total_delta))

    def _read_ram(self):
        values = {}
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    key, _, rest = line.partition(":")
                    if key in ("MemTotal", "MemAvailable"):
                        values[key] = int(rest.split()[0])
                    if len(values) == 2:
                        break
        except (OSError, ValueError):
            return self.ram

        total = values.get("MemTotal", 0)
        if not total:
            return self.ram
        return round(100 * (1 - values.get("MemAvailable", 0) / total))

    def _read_temp(self):
        if not self._k10temp:
            return 0
        try:
            with open(os.path.join(self._k10temp, "temp1_input")) as f:
                return round(int(f.read()) / 1000)
        except (OSError, ValueError):
            return self.temp

    def _read_battery(self):
        try:
            with open("/sys/class/power_supply/BAT0/capacity") as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return self.battery


class CuteIcon(Box):
    """the two-label pill from the eww bar: coloured glyph, then the value"""

    def __init__(self, readings, glyph, getter, suffix="", extra_class=None, **kwargs):
        classes = ["cuteIcon"] + ([extra_class] if extra_class else [])
        super().__init__(style_classes=classes, space_evenly=False, **kwargs)

        self.value = Label(style_classes="txt")
        self.children = [Label(label=glyph), self.value]

        readings.subscribe(lambda: self.value.set_label(f"{getter()}{suffix}"))


def cpu(readings):
    return CuteIcon(readings, "\uf4bc", lambda: readings.cpu, "%", "cpuIcon")


def ram(readings):
    return CuteIcon(readings, "\uebe4", lambda: readings.ram, "%", "ramIcon")


def temperature(readings):
    return CuteIcon(readings, "\uf2c9", lambda: readings.temp, "", "tempIcon")


def battery(readings):
    return CuteIcon(readings, "\uf0e7", lambda: readings.battery, "%", "tempIcon")
