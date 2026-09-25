# Builds the dock json from one `xprop -id` dump per window (see taskbar.sh).
# Input: "@ <id>" before each window's WM_CLASS / WM_NAME / _NET_WM_STATE /
# _GTK_APPLICATION_ID lines. Writes the multi window caches for rofi_menu.sh.

function san(s) {
	gsub(/[ .-]/, "_", s)
	return tolower(s)
}

BEGIN {
	# viewable windows (mapped, current workspace), decimal ids from xdotool
	nv = split(onscreen, onlist, " ")
	for (i = 1; i <= nv; i++)
		viewable[sprintf("0x%x", onlist[i])] = 1

	while ((getline line < icons) > 0) {
		sub(/[ \t]+$/, "", line)
		i = index(line, "=")
		if (i > 1)
			icon[substr(line, 1, i - 1)] = substr(line, i + 1)
	}

	while ((getline line < pinned) > 0)
		json = json line "\n"
}

/^@ / { id = $2; ids[++n] = id; next }
/^WM_CLASS\(/ { split($0, q, "\""); class[id] = san(q[4]); next }
/^_GTK_APPLICATION_ID\(/ { split($0, q, "\""); gtk[id] = san(q[2]); next }
/^_NET_WM_STATE\(/ { hidden[id] = ($0 ~ /_NET_WM_STATE_HIDDEN/); next }
/^WM_NAME\(/ {
	v = $0
	sub(/^[^=]*= "/, "", v)
	sub(/"$/, "", v)
	name[id] = v
	next
}

END {
	for (k = 1; k <= n; k++) {
		id = ids[k]
		c = class[id]
		if (c == "")
			continue

		if (!(c in count)) {
			order[++classes] = c
			first[c] = id
		}

		count[c]++
		wins[c] = wins[c] (wins[c] == "" ? "" : " ") id
		names[c] = names[c] (names[c] == "" ? "" : "\n") name[id]
		if (id in viewable)
			visible[c]++
		if (id == active)
			active_class = c
	}

	sub(/[ \t\n]*\][ \t\n]*$/, "", json)
	empty = (json ~ /^[ \t\n]*\[[ \t\n]*$/)

	for (k = 1; k <= classes; k++) {
		c = order[k]
		id = first[c]

		if (count[c] == 1)
			state = hidden[id] ? "minimized" : (id == active ? "focused" : "unfocused")
		else
			state = c == active_class ? "focused" : (visible[c] ? "unfocused" : "minimized")

		if (count[c] > 1) {
			printf "%s\n", wins[c] > (cache "/multi_win/" c)
			close(cache "/multi_win/" c)
			printf "%s\n", names[c] > (cache "/multi_winames/" c)
			close(cache "/multi_winames/" c)
		}

		key = "\"name\": \"" c "\""
		p = index(json, key)
		if (p) {
			json = substr(json, 1, p - 1) key ", \"id\" : \"" id "\", \"state\": \"" state "\"" substr(json, p + length(key))
			continue
		}

		path = (c in icon) ? icon[c] : icon[gtk[id]]
		if (path == "")
			continue

		json = json (empty ? "" : ",") "{\n          \"name\": \"" c "\",\n          \"icon\": \"" path "\",\n          \"id\": \"" id "\",\n          \"state\": \"" state "\"\n          }"
		empty = 0
	}

	print json " ]"
}
