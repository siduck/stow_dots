#!/bin/dash

ewwconf="/home/$USER/.config/eww"
cache="$ewwconf/cache"

# Generates the dock json: pinned apps plus open windows, with icon, id and state
gen_taskbar() {
	root=$(xprop -root _NET_CLIENT_LIST _NET_ACTIVE_WINDOW)
	win_ids=$(echo "$root" | sed -n 's/^_NET_CLIENT_LIST(WINDOW): window id # //p')
	active=$(echo "$root" | sed -n 's/^_NET_ACTIVE_WINDOW(WINDOW): window id # //p')

	echo "$win_ids" >"$cache/win_ids"
	echo "$active" >"$cache/active_winid"
	rm -f "$cache"/multi_win/* "$cache"/multi_winames/*

	# apps with several windows count as minimized when none of them is on screen
	onscreen=$(xdotool search --onlyvisible --name . 2>/dev/null | tr '\n' ' ')

	# one xprop per window, everything else in a single awk pass
	json=$(
		for id in $(echo "$win_ids" | tr -d ,); do
			echo "@ $id"
			xprop -id "$id" WM_CLASS WM_NAME _NET_WM_STATE _GTK_APPLICATION_ID 2>/dev/null
		done | awk -v active="$active" -v onscreen="$onscreen" -v cache="$cache" \
			-v icons="$cache/icons" -v pinned="$cache/pinned_apps" \
			-f "$ewwconf/scripts/taskbar.awk"
	)

	eww update apps="$json"
}

# mtimes of the .desktop dirs - changes when an app is installed/removed
appdirs_state() {
	stat -c '%Y' /usr/share/applications /usr/local/share/applications "/home/$USER/.local/share/applications" 2>/dev/null
}

update_taskbar() {
	# new/removed .desktop files -> rebuild icon cache first
	apps=$(appdirs_state)
	if [ "$apps" != "$(cat "$cache/appdirs_state" 2>/dev/null)" ]; then
		"$ewwconf/scripts/gen_icons.sh"
		echo "$apps" >"$cache/appdirs_state"
	fi

	gen_taskbar
}

update_taskbar

# like tint2/xfce4-panel: X pushes root property changes, nothing is polled
xprop -root -spy _NET_CLIENT_LIST _NET_ACTIVE_WINDOW _NET_CURRENT_DESKTOP |
	while read -r _; do
		update_taskbar
	done &
spy=$!

# pin/unpin (utils.sh) asks for a refresh with USR1
echo $$ >"$cache/taskbar.pid"
trap update_taskbar USR1

# wait returns early whenever USR1 runs the trap; stop once X (and so xprop) is gone
while kill -0 "$spy" 2>/dev/null; do
	wait "$spy"
done
