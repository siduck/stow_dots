#!/bin/sh

ewwconf="$HOME/.config/eww"

mouse_x=${1:-0}

themes=$(ls "$ewwconf/css/themes/" | sed 's/\.scss$//')

# gap between the menu's bottom edge and the dock
gap=10

# menu width must match `width` in rofi/menu.rasi
menu_width=300

dock_id=$(xdotool search --name "Eww - dock" | head -1)
dock_top=$(xdotool getwindowgeometry "$dock_id" 2>/dev/null | awk '/Position/ {split($2, a, ","); print a[2]}')
[ -z "$dock_top" ] && dock_top=$(xdotool getdisplaygeometry | cut -d' ' -f2)

screen_width=$(xdotool getdisplaygeometry | cut -d' ' -f1)
screen_height=$(xdotool getdisplaygeometry | cut -d' ' -f2)

# menu/rofi is anchored bottom-left (see menu.rasi `location: 7`), so yoffset
# is measured from the screen's bottom edge, not the window's own (guessed)
# height -- this keeps the gap exact no matter how tall rofi actually renders
yaxis=$(( (dock_top - gap) - screen_height ))
xaxis=$(( mouse_x - (menu_width / 2) ))

# clamp horizontally so the menu never spills off screen
[ "$xaxis" -lt 0 ] && xaxis=0
max_x=$(( screen_width - menu_width ))
[ "$xaxis" -gt "$max_x" ] && xaxis=$max_x

selected_theme=$(echo "$themes" | rofi -config "$ewwconf/rofi/menu.rasi" -dmenu -i -p "Theme " \
    -xoffset "$xaxis" -yoffset "$yaxis" -no-fixed-num-lines)

[ -n "$selected_theme" ] && set_theme "$selected_theme"
