#!/bin/sh

export XDG_CURRENT_DESKTOP=chadwm
export XDG_SESSION_TYPE=x11

set_theme espresso startup &

xset r rate 200 50 &
picom &
xsettingsd &

pipewire &
while [ ! -e "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/pipewire-0" ]; do sleep 0.1; done
wireplumber &
pipewire-pulse &

pkill -f chadwm/scripts/bar.sh
~/.config/chadwm/scripts/bar.sh 2>~/.cache/chadwm-bar.log &

libinput-gestures-setup start &

while type chadwm >/dev/null; do chadwm 2>>~/.cache/chadwm.log && continue || break; done
