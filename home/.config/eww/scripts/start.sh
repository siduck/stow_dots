#!/bin/dash

ewwconf="/home/$USER/.config/eww"
# one taskbar loop per session, not one per restart
pkill -f "$ewwconf/scripts/taskbar.sh"
$ewwconf/scripts/taskbar.sh &
eww open dock &
