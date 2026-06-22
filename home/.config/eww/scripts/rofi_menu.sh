#!/bin/dash

ewwconf="/home/$USER/.config/eww"

win_ids=$1
win_names=$2

win_count=$(echo $win_ids | wc -w)

yaxis=$(( $4 - ((win_counter + 5) * 30 ) ))
xaxis=$(( $3 ))


# # Use Rofi to display the list of win IDs and select one
selected_index=$(echo "$win_names" | rofi -config $ewwconf/rofi/menu.rasi -dmenu -i -p "  Search "  -xoffset $xaxis -yoffset $yaxis -format i -hover-select -no-fixed-num-lines )
selected_index=$(($selected_index + 1))

selected_win=$(echo "$win_ids" | cut -d ' ' -f $selected_index)

echo $selected_win | tr -d ","

get_win_state() {
	win_state="unfocused"
	net_wm_state=$(xprop -id "$1" _NET_WM_STATE | cut -d'=' -f2)
	active_win=$(<$ewwconf/cache/active_winid)

	if [ "$net_wm_state" = " _NET_WM_STATE_HIDDEN" ]; then
		win_state="minimized"
	elif [ "$1" = "$active_win" ]; then
		win_state="focused"
	fi

	echo $win_state
}

win_state=$(get_win_state $selected_win)

"$(dirname "$0")/utils.sh" toggle_win $selected_win $win_state
