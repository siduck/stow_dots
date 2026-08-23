"""
Resolves the scss theme files in ~/.config/eww/css/themes into plain GTK css.

Fabric has no sass compiler, so the handful of scss features the stylesheet
actually uses (variables, lighten/darken/mix) are implemented here. That keeps
all 18 existing theme files usable as-is, and keeps `set_theme` untouched --
it writes ~/.config/theme, which is what we read and watch.
"""

import os
import re
import colorsys

THEME_FILE = os.path.expanduser("~/.config/theme")
THEMES_DIR = os.path.expanduser("~/.config/eww/css/themes")

_VAR_RE = re.compile(r"^\s*\$([\w-]+)\s*:\s*(.+?)\s*;?\s*$")
_CALL_RE = re.compile(r"\b(lighten|darken|mix)\(")
_REF_RE = re.compile(r"\$([\w-]+)")


def _to_rgb(value):
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in rgb)


def _lighten(rgb, amount):
    h, l, s = colorsys.rgb_to_hls(*[c / 255 for c in rgb])
    l = max(0.0, min(1.0, l + amount / 100))
    return tuple(c * 255 for c in colorsys.hls_to_rgb(h, l, s))


def _mix(rgb1, rgb2, weight):
    w = weight / 100
    return tuple(a * w + b * (1 - w) for a, b in zip(rgb1, rgb2))


def _split_args(text):
    """split on top-level commas, so nested calls survive"""
    args, depth, current = [], 0, ""
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        args.append(current.strip())
    return args


def _strip_kwarg(arg):
    # scss allows `lighten($color: $bg, $amount: 4)`
    if ":" in arg and arg.lstrip().startswith("$"):
        return arg.split(":", 1)[1].strip()
    return arg


def _resolve(value, variables):
    """resolve $refs and lighten/darken/mix calls down to a hex literal"""
    value = _REF_RE.sub(lambda m: variables.get(m.group(1), m.group(0)), value)

    while True:
        match = _CALL_RE.search(value)
        if not match:
            return value.strip()

        # walk to the matching close paren
        depth, end = 0, None
        for i in range(match.end() - 1, len(value)):
            if value[i] == "(":
                depth += 1
            elif value[i] == ")":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end is None:
            return value.strip()

        name = match.group(1)
        args = [_strip_kwarg(a) for a in _split_args(value[match.end() : end])]
        args = [_resolve(a, variables) for a in args]

        try:
            if name in ("lighten", "darken"):
                amount = float(args[1].rstrip("%"))
                rgb = _lighten(_to_rgb(args[0]), amount if name == "lighten" else -amount)
            else:
                weight = float(args[2].rstrip("%")) if len(args) > 2 else 50.0
                rgb = _mix(_to_rgb(args[0]), _to_rgb(args[1]), weight)
            replacement = _to_hex(rgb)
        except (ValueError, IndexError):
            replacement = args[0] if args else "#000000"

        value = value[: match.start()] + replacement + value[end + 1 :]


def current_theme():
    try:
        with open(THEME_FILE) as f:
            for line in f:
                if line.startswith("theme="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return "espresso"


def palette(theme=None):
    """{'bg': '#141b1e', 'bg-2': '#1e2528', ...} for the active theme"""
    theme = theme or current_theme()
    path = os.path.join(THEMES_DIR, theme + ".scss")
    variables = {}
    try:
        with open(path) as f:
            for line in f:
                match = _VAR_RE.match(line)
                if match:
                    variables[match.group(1)] = _resolve(match.group(2), variables)
    except OSError:
        pass
    return variables


def compile_stylesheet(path, theme=None):
    """read a stylesheet written in the eww.scss dialect, return GTK css"""
    with open(path) as f:
        source = f.read()

    variables = palette(theme)
    # longest name first so $bg-4 is not eaten by $bg
    for name in sorted(variables, key=len, reverse=True):
        source = source.replace("$" + name, variables[name])
    return _resolve(source, variables)
