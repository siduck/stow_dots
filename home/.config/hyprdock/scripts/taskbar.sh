#!/bin/sh
ewwconf="$HOME/.config/hyprdock"

process() {
    pinned=$(cat "$ewwconf/cache/pinned_apps" 2>/dev/null || echo '[]')

    icon_map='{"footclient":"foot","pcmanfm":"system-file-manager","xfce4-taskmanager":"org.xfce.taskmanager","brave-browser":"brave","brave-origin-nightly":"brave"}'

    running=$(echo "$1" | jq -c --argjson imap "$icon_map" '
        group_by(.app_id) | map({
            app_id:    .[0].app_id,
            title:     ((map(select(.active)) | .[0].title) // .[0].title),
            active:    (map(.active)    | any),
            minimized: (map(.minimized) | all),
            count:     length,
            id:        .[0].id,
            cmd:       "",
            icon_name: ($imap[.[0].app_id] // .[0].app_id)
        })
    ')

    # prepend pinned apps that are NOT currently running
    # pinned_apps uses "name" key (original X11 format)
    # derive icon_name from icon path basename without extension
    echo "$running" | jq -c --argjson p "$pinned" '
        . as $r |
        ($r | map(.app_id)) as $ids |
        ($p | map(select((.name // .app_id) | IN($ids[]) | not))
            | map({
                app_id:    (.name // .app_id),
                title:     (.name // .app_id),
                active:    false,
                minimized: false,
                count:     0,
                id:        -1,
                cmd:       (.cmd // ""),
                icon_name: (if .icon != null then (.icon | split("/") | last | sub("\\.[^.]+$";"")) else (.name // .app_id) end)
              })
        ) + $r
    '
}

wlr-apps -mjq 1 | while IFS= read -r line; do
    process "$line"
done
