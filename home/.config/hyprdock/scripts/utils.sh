#!/bin/sh
ewwconf="$HOME/.config/hyprdock"
. "$ewwconf/scripts/fuzzel_pos.sh"

get_mousecoords() {
    pos=$(hyprctl cursorpos)
    mouse_x=$(echo "$pos" | cut -d',' -f1 | tr -d ' ')
    mouse_y=$(echo "$pos" | cut -d',' -f2 | tr -d ' ')
}

taskicon_click() {
    app_id="$1"
    id="$2"
    active="$3"
    minimized="$4"
    cmd="$5"

    # pinned but not running
    if [ "$id" = "-1" ]; then
        $cmd &
        return
    fi

    # count windows for this app_id
    count=$(wlr-apps -j | jq "[.[] | select(.app_id == \"$app_id\")] | length")

    if [ "$count" -le 1 ]; then
        if [ "$active" = "true" ]; then
            wlr-apps -x "m $id"
        else
            wlr-apps -x "f $id"
        fi
    else
        # multi-window rofi picker
        wins=$(wlr-apps -j | jq -r ".[] | select(.app_id == \"$app_id\") | \"\(.id)|\(.title)\"")
        titles=$(printf '%s\n' "$wins" | cut -d'|' -f2-)
        get_mousecoords
        fuzzel_calc_pos "$mouse_x"
        selected=$(printf '%s\n' "$titles" | fuzzel --dmenu \
            --prompt="$app_id: " --anchor=bottom-left \
            --x-margin="$fuzzel_xoff" --y-margin="$fuzzel_yoff" \
            --minimal-lines --width=30)
        [ -z "$selected" ] && return
        sel_id=$(printf '%s\n' "$wins" | grep "|$selected$" | cut -d'|' -f1 | head -1)
        [ -n "$sel_id" ] && wlr-apps -x "f $sel_id"
    fi
}

pin_app_toggle() {
    current=$(eww -c "$ewwconf" get clicked_win)
    if [ "$current" = "${1}_on" ]; then
        eww -c "$ewwconf" update clicked_win="${1}_off"
    else
        eww -c "$ewwconf" update clicked_win="${1}_on"
    fi
}

pin_app() {
    app_id="$1"
    cmd="$2"
    file="$ewwconf/cache/pinned_apps"

    # try to resolve real binary via hyprctl
    if [ -z "$cmd" ]; then
        pid=$(hyprctl clients -j | jq -r ".[] | select(.class == \"$app_id\") | .pid" | head -1)
        [ -n "$pid" ] && cmd=$(readlink -f "/proc/$pid/exe" 2>/dev/null)
        [ -z "$cmd" ] && cmd="$app_id"
    fi

    jq --arg a "$app_id" --arg c "$cmd" \
        '. + [{name: $a, icon: null, cmd: $c}]' "$file" > /tmp/pa_tmp && mv /tmp/pa_tmp "$file"
    eww -c "$ewwconf" update clicked_win=""
}

unpin_app() {
    app_id="$1"
    file="$ewwconf/cache/pinned_apps"
    jq --arg a "$app_id" 'del(.[] | select(.app_id == $a))' "$file" \
        > /tmp/pa_tmp && mv /tmp/pa_tmp "$file"
    eww -c "$ewwconf" update clicked_win=""
}

get_pkgupdates() {
    updates=$(doas xbps-install -un 2>/dev/null | wc -l)
    echo "  $updates"
}

run_theme_switcher() {
    get_mousecoords
    "$(dirname "$0")/theme_switcher.sh" "$mouse_x" "$mouse_y"
}

toggle_volume() {
    val=$(eww -c "$ewwconf" get volume_slider)
    if [ "$val" = "true" ]; then
        eww -c "$ewwconf" update volume_slider=false
    else
        eww -c "$ewwconf" update volume_slider=true
    fi
}

"$@"
