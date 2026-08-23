# fabric dock

Port of `~/.config/eww`. Same layout, same stylesheet, same themes, same rofi
helper scripts. The eww config is untouched, so both can be compared.

## install

Fabric is not in the Void repos, and its `requirements.txt` pins
`PyGObject==3.50.0` while Void ships 3.56.2. Don't let pip build PyGObject --
use the packaged one and let fabric see it:

    doas xbps-install -S python3-xlib gobject-introspection gtk+3-devel

    # a venv that can see the system gi, built on the system python
    # (the existing venv/ here was made with uv's python and
    #  include-system-site-packages=false, so it can never see gi -- delete it)
    rm -rf ~/.config/fabric/venv
    /usr/bin/python3 -m venv --system-site-packages ~/.config/fabric/venv
    ~/.config/fabric/venv/bin/pip install click loguru
    ~/.config/fabric/venv/bin/pip install --no-deps \
        git+https://github.com/Fabric-Development/fabric.git

The shebang in `config.py` points at that venv, so it runs directly.

`psutil` is not needed -- readings come from `/proc` directly.
The audio service (`libcvc`) is not needed -- volume goes through `pactl`.

## run

    ~/.config/fabric/config.py

To swap it in for eww at login, replace the `eww/scripts/start.sh` line in your
autostart with this one.

## what changed from the eww config

- `scripts/taskbar.sh` is gone. It was a `while true` with no sleep running
  `xprop -root` every iteration -- ~600 process spawns a second, permanently.
  `modules/xevents.py` holds one X connection on the GLib main loop and only
  does work when the server sends a PropertyNotify.
- `scripts/gen_icons.sh` and `cache/icons` are gone. Icons come from Gio's
  desktop app database, which honours `StartupWMClass` properly.
- The `cache/` files (win_ids, active_winid, multi_win, refresh_dock) are gone;
  that state lives in the process now.
- Volume follows changes made elsewhere -- `pactl subscribe` instead of a
  hardcoded starting value of 50.
- Clock, cpu, ram, temp and battery no longer fork anything. One 2s timer
  reads `/proc` and `/sys`.
- `xdotool` is no longer called for activate/minimize/workspace switching;
  those are EWMH client messages now.

- rofi is gone. `rofi_menu.sh` and `theme_switcher.sh` each spawned a second
  GUI process plus three `xdotool` calls to locate the dock; `modules/popup.py`
  is a GTK window in the process we already have. Nothing is left in shell.
- Icons are rasterised once into `cache/icons.bin` as raw RGBA. Rendering one
  Papirus SVG pulls librsvg in and costs 8.6 MB -- more than every pixbuf
  combined -- so warm starts wrap the cached bytes and no image loader ever
  loads. Icons render on their native 32px grid, not squeezed to 30, which is
  what made them look soft.

Still a subprocess, deliberately: `pactl subscribe` (one sleeping process, so
volume follows changes made elsewhere) and the periodic package-update count
(xbps has no library binding).

## files

    config.py            entry point (executable), window assembly, theming
    style.css            eww.scss with the nesting flattened
    modules/theme.py     resolves the eww scss themes ($vars, lighten, mix)
    modules/xevents.py   the X11 connection -- replaces taskbar.sh
    modules/dock.py      taskbar, pinned apps, icon lookup
    modules/workspaces.py
    modules/sysinfo.py   cpu/ram/temp/battery from /proc and /sys
    modules/volume.py    pactl + pactl subscribe
    modules/misc.py      distro, power, wifi, updates, theme switcher
    modules/popup.py     native picker popup -- replaces rofi
    modules/strut.py     _NET_WM_STRUT_PARTIAL (X11Window has no :reserve)
    cache/icons.bin      rasterised icons, raw RGBA
    bench.sh             rss/pss/cpu/fork rate of whichever bar is up
