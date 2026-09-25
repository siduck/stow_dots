#!/bin/sh

ewwconf="$HOME/.config/eww"

mouse_x=${1:-0}

themes=$(ls "$ewwconf/css/themes/" | sed 's/\.scss$//')

# gap between the menu's bottom edge and the dock
gap=10

# menu width must match `width` in rofi/menu.rasi
menu_width=300

dock_id=$(xdotool search --name "Eww - dock" | head -1)

# rofi's -xoffset/-yoffset are relative to the monitor it opens on, but the
# dock position and the pointer are root coordinates. Convert everything to
# the dock monitor's own coordinates, otherwise any monitor not at +0+0 (e.g.
# eDP stacked below the external) pushes the menu off screen.
unset X Y WIDTH HEIGHT
eval "$(xdotool getwindowgeometry --shell "$dock_id" 2>/dev/null)"
set -- $(xrandr --listmonitors | tail -n +2 | sed 's:/[0-9]*::g' |
	awk -v cx="$((${X:-0} + ${WIDTH:-0} / 2))" -v cy="$((${Y:-0} + ${HEIGHT:-0} / 2))" '{
		split($3, a, /[x+]/)
		if (cx >= a[3] && cx < a[3] + a[1] && cy >= a[4] && cy < a[4] + a[2]) {
			print a[3], a[4], a[1], a[2]; exit
		}
	}')
mon_x=${1:-0} mon_y=${2:-0}
screen_width=${3:-$(xdotool getdisplaygeometry | cut -d' ' -f1)}
screen_height=${4:-$(xdotool getdisplaygeometry | cut -d' ' -f2)}

dock_top=$(( ${Y:-$screen_height} - mon_y ))
mouse_x=$(( mouse_x - mon_x ))

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
