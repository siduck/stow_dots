#!/bin/sh

ewwconf="$HOME/.config/eww"

mouse_x=${1:-0}

themes=$(ls "$ewwconf/css/themes/" | sed 's/\.scss$//')
theme_count=$(echo "$themes" | wc -l)

# gap between the menu's bottom edge and the dock
gap=10

# menu width must match `width` in rofi/menu.rasi
menu_width=300
menu_height=$(( (theme_count + 2) * 30 ))

dock_id=$(xdotool search --name "Eww - dock" | head -1)
dock_top=$(xdotool getwindowgeometry "$dock_id" 2>/dev/null | awk '/Position/ {split($2, a, ","); print a[2]}')
[ -z "$dock_top" ] && dock_top=$(xdotool getdisplaygeometry | cut -d' ' -f2)

screen_width=$(xdotool getdisplaygeometry | cut -d' ' -f1)

# menu sits a `gap` above the dock; centered horizontally over the clicked icon
yaxis=$(( dock_top - gap - menu_height ))
xaxis=$(( mouse_x - (menu_width / 2) ))

# clamp horizontally so the menu never spills off screen
[ "$xaxis" -lt 0 ] && xaxis=0
max_x=$(( screen_width - menu_width ))
[ "$xaxis" -gt "$max_x" ] && xaxis=$max_x

selected_theme=$(echo "$themes" | rofi -config "$ewwconf/rofi/menu.rasi" -dmenu -i -p "Theme " \
    -xoffset "$xaxis" -yoffset "$yaxis" -no-fixed-num-lines)

[ -n "$selected_theme" ] && set_theme "$selected_theme"
