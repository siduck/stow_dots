#!/bin/sh

theme_name="$1"
theme_file="$HOME/.config/eww/css/themes/${theme_name}.scss"
fuzzel_ini="$HOME/.config/fuzzel/fuzzel.ini"

[ -f "$theme_file" ] || { echo "theme not found: $theme_file" >&2; exit 1; }

mkdir -p "$HOME/.config/fuzzel"

awk -v outfile="$fuzzel_ini" '
function hex2int(h,    i,c,r) {
    r = 0; h = tolower(h)
    for (i = 1; i <= length(h); i++) {
        c = index("0123456789abcdef", substr(h,i,1)) - 1
        r = r * 16 + c
    }
    return r
}

function clamp(v,lo,hi) { return v<lo ? lo : (v>hi ? hi : v) }

function hue2rgb(p,q,t) {
    if (t < 0) t += 1
    if (t > 1) t -= 1
    if (t < 1/6) return p + (q-p)*6*t
    if (t < 0.5) return q
    if (t < 2/3) return p + (q-p)*(2/3-t)*6
    return p
}

function adjust(hex, delta,    r,g,b,rn,gn,bn,mx,mn,l,s,h,d,q,p) {
    r = hex2int(substr(hex,1,2))
    g = hex2int(substr(hex,3,2))
    b = hex2int(substr(hex,5,2))
    rn=r/255; gn=g/255; bn=b/255
    mx = (rn>gn ? (rn>bn?rn:bn) : (gn>bn?gn:bn))
    mn = (rn<gn ? (rn<bn?rn:bn) : (gn<bn?gn:bn))
    l  = (mx+mn)/2
    if (mx == mn) { h=0; s=0 }
    else {
        d = mx-mn
        s = l>0.5 ? d/(2-mx-mn) : d/(mx+mn)
        if      (mx==rn) { h=(gn-bn)/d; if(gn<bn) h+=6 }
        else if (mx==gn)   h=(bn-rn)/d+2
        else               h=(rn-gn)/d+4
        h /= 6
    }
    l = clamp(l+delta, 0, 1)
    if (s == 0) { r=g=b=l*255 }
    else {
        q = l<0.5 ? l*(1+s) : l+s-l*s
        p = 2*l-q
        r = hue2rgb(p,q,h+1/3)*255
        g = hue2rgb(p,q,h    )*255
        b = hue2rgb(p,q,h-1/3)*255
    }
    return sprintf("%02x%02x%02x", int(r+0.5), int(g+0.5), int(b+0.5))
}

/^\$[a-zA-Z]/ {
    line = $0
    gsub(/[ \t;]/, "", line)
    colon = index(line, ":")
    name  = substr(line, 2, colon-2)   # strip leading $
    val   = substr(line, colon+1)

    if (val ~ /^#[0-9a-fA-F]{6}$/) {
        c[name] = substr(val, 2)

    } else if (val ~ /^lighten\(/) {
        tmp = val; sub(/.*\$color:\$/, "", tmp); sub(/[^a-zA-Z0-9_-].*/, "", tmp)
        base = tmp
        tmp2 = val; sub(/.*\$amount:/, "", tmp2); sub(/[^0-9].*/, "", tmp2)
        if (base in c) c[name] = adjust(c[base],  tmp2/100)

    } else if (val ~ /^darken\(/) {
        tmp = val; sub(/.*\$color:\$/, "", tmp); sub(/[^a-zA-Z0-9_-].*/, "", tmp)
        base = tmp
        tmp2 = val; sub(/.*\$amount:/, "", tmp2); sub(/[^0-9].*/, "", tmp2)
        if (base in c) c[name] = adjust(c[base], -tmp2/100)
    }
}

END {
    bg     = ("bg"     in c) ? c["bg"]     : "1e1e1e"
    bg2    = ("bg-2"   in c) ? c["bg-2"]   : "282828"
    bg4    = ("bg-4"   in c) ? c["bg-4"]   : "3c3c3c"
    fg     = ("fg"     in c) ? c["fg"]     : "d4d4d4"
    accent = ("orange" in c) ? c["orange"] : \
             ("blue"   in c) ? c["blue"]   : "d08b65"

    print "[main]"                            > outfile
    print "font=Inter:size=11"                > outfile
    print "lines=15"                          > outfile
    print "width=30"                          > outfile
    print "horizontal-pad=20"                > outfile
    print "vertical-pad=12"                   > outfile
    print "inner-pad=10"                      > outfile
    print "line-height=18"                    > outfile
    print "border-width=2"                    > outfile
    print "border-radius=8"                   > outfile
    print ""                                  > outfile
    print "[colors]"                          > outfile
    print "background="   bg     "ff"         > outfile
    print "text="         fg     "ff"         > outfile
    print "match="        accent "ff"         > outfile
    print "selection="    bg2    "ff"         > outfile
    print "selection-text=" fg   "ff"         > outfile
    print "selection-match=" accent "ff"      > outfile
    print "border="       bg4    "ff"         > outfile
    print "input="        fg     "ff"         > outfile
}
' "$theme_file"
