#!/bin/sh
# output current workspace (0-indexed), then stream changes via Hyprland socket2
SOCK="/run/user/${UID:-1000}/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock"
hyprctl activeworkspace -j | jq '.id - 1'
socat -u UNIX-CONNECT:"$SOCK" - 2>/dev/null \
    | stdbuf -oL grep -o 'workspace>>[0-9]*' \
    | stdbuf -oL sed 's/workspace>>//' \
    | while IFS= read -r ws; do
        echo $((ws - 1))
      done
