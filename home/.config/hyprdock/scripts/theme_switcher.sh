#!/bin/sh

ewwconf="$HOME/.config/hyprdock"
. "$ewwconf/scripts/fuzzel_pos.sh"

fuzzel_calc_pos "${1:-0}"

count=$(ls "$ewwconf/css/themes/" | wc -l)
selected=$(ls "$ewwconf/css/themes/" | sed 's/\.scss$//' | fuzzel --dmenu \
    --prompt="Theme: " --anchor=bottom-left \
    --x-margin="$fuzzel_xoff" --y-margin="$fuzzel_yoff" \
    --width=30 --lines="$count")

[ -z "$selected" ] && exit

sed -i "s|@import \"./css/themes/.*\";|@import \"./css/themes/$selected.scss\";|" \
    "$ewwconf/eww.scss"
eww -c "$ewwconf" reload
