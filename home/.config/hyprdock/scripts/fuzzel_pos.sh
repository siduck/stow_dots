#!/bin/sh
# Source this file, then call: fuzzel_calc_pos <mouse_x>
# Sets $fuzzel_xoff and $fuzzel_yoff for --anchor=bottom-left positioning

fuzzel_calc_pos() {
    _mx="${1:-0}"
    _ini="$HOME/.config/fuzzel/fuzzel.ini"

    # fuzzel anchors to the usable area bottom (exclusive zone boundary = dock top),
    # so y-margin is simply the gap we want above the dock icons
    fuzzel_yoff=10

    # half-width: (width_chars * char_advance + 2 * h_pad) / 2
    # char_advance ≈ font_size_pt * (96/72) * 0.58  (Inter proportional)
    _w=$(awk  -F= '/^width=/{print $2}'          "$_ini" 2>/dev/null); _w=${_w:-30}
    _hp=$(awk -F= '/^horizontal-pad=/{print $2}' "$_ini" 2>/dev/null); _hp=${_hp:-20}
    _fs=$(awk -F= '/^font=/{gsub(/.*size=/,""); gsub(/[^0-9].*/,""); print}' "$_ini" 2>/dev/null)
    _fs=${_fs:-11}

    _half=$(awk "BEGIN{ printf \"%d\", ($_w * $_fs * 1.333 * 0.58 + $_hp * 2) / 2 + 0.5 }")

    fuzzel_xoff=$(( _mx - _half ))
    [ "$fuzzel_xoff" -lt 0 ] && fuzzel_xoff=0
}
