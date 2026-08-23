#!/bin/sh
# dwm-style focusmon for openbox: focus the next/prev monitor
# usage: focusmon.sh next|prev
#
# the pointer is the "selected monitor" marker: openbox has no per-monitor
# focus, and rc.xml places new windows on the monitor under the mouse.

dir=${1:-next}

# "X Y W H" per monitor, ordered left to right
mons=$(xrandr --listmonitors | tail -n +2 | sed 's:/[0-9]*::g' |
	awk '{split($3, a, /[x+]/); print a[3], a[4], a[1], a[2]}' | sort -n)

n=$(echo "$mons" | wc -l)
[ "$n" -lt 2 ] && exit 0

pos=$(xdotool getmouselocation --shell | awk -F= '/^X=/{x=$2} /^Y=/{y=$2} END {print x, y}')

i=$(echo "$mons" | awk -v cx="${pos% *}" -v cy="${pos#* }" \
	'cx >= $1 && cx < $1 + $3 && cy >= $2 && cy < $2 + $4 {print NR; exit}')
[ -z "$i" ] && i=1

if [ "$dir" = prev ]; then
	t=$((i - 1))
	[ "$t" -lt 1 ] && t=$n
else
	t=$((i + 1))
	[ "$t" -gt "$n" ] && t=1
fi

set -- $(echo "$mons" | sed -n "${t}p")
mx=$1 my=$2 mw=$3 mh=$4

# topmost normal window on that monitor (stacking list runs bottom to top)
desk=$(xdotool get_desktop)
win= wx= wy=
for w in $(xprop -root _NET_CLIENT_LIST_STACKING | sed 's/.*# //; s/,//g'); do
	# sticky windows report failure or -1; they count as being on every desktop
	wd=$(xdotool get_desktop_for_window "$w" 2>/dev/null) || wd=-1
	case $wd in
	"$desk" | -1 | 4294967295) ;;
	*) continue ;;
	esac

	# docks, panels and the desktop are not focus targets
	case $(xprop -id "$w" _NET_WM_WINDOW_TYPE 2>/dev/null) in
	*_DOCK* | *_DESKTOP* | *_SPLASH*) continue ;;
	esac

	unset X Y WIDTH HEIGHT
	eval "$(xdotool getwindowgeometry --shell "$w" 2>/dev/null)"
	[ -z "$WIDTH" ] && continue
	cx=$((X + WIDTH / 2))
	cy=$((Y + HEIGHT / 2))
	if [ $cx -ge $mx ] && [ $cx -lt $((mx + mw)) ] &&
		[ $cy -ge $my ] && [ $cy -lt $((my + mh)) ]; then
		win=$w wx=$cx wy=$cy
	fi
done

if [ -n "$win" ]; then
	xdotool windowactivate "$win"
	xdotool mousemove "$wx" "$wy"
else
	xdotool mousemove $((mx + mw / 2)) $((my + mh / 2))
fi
