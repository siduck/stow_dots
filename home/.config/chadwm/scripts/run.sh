#!/bin/sh

export XDG_CURRENT_DESKTOP=chadwm
export XDG_SESSION_TYPE=x11

set_theme chocolate startup &

xset r rate 200 50 &
picom &

pipewire & wireplumber & pipewire-pulse & 

~/.config/chadwm/scripts/bar.sh &

libinput-gestures-setup start &

while type chadwm >/dev/null; do chadwm && continue || break; done
