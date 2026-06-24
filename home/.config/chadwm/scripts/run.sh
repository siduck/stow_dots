#!/bin/sh

set_theme everforest &

xset r rate 200 50 &
picom &

pipewire & wireplumber & pipewire-pulse & 

./bar.sh &

libinput-gestures-setup start &

while type chadwm >/dev/null; do chadwm && continue || break; done
