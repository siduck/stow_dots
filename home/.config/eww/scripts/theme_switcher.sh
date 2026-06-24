#!/bin/dash

ewwconf="/home/$USER/.config/eww"

counter=0

for file in ~/.config/eww/css/themes/*; do
	filename="${file##*/}" # Remove the path and keep just the filename
	theme="${filename%.*}" # Remove the extension
	themes="$themes$theme\n"
	counter=$((counter + 1))
done

themes="${themes%\\n*}"

yaxis=$(( $2 - ((counter + 1) * 35 ) ))
xaxis=$(( $1 - 10 ))

# # Use Rofi to display the list of win IDs and select one
selected_theme=$(echo "$themes" | rofi -config "$ewwconf/rofi/menu.rasi" -dmenu -i -p "Search " -xoffset "$xaxis" -yoffset "$yaxis" -hover-select -no-fixed-num-lines)

set_theme "$selected_theme"
