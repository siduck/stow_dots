#!/bin/dash
# Compares the running bar against the other one. Run it once with eww up,
# once with fabric up; the numbers are directly comparable.
#
#   rss  - total pages mapped, shared libs counted in full
#   pss  - rss with shared pages split across users; the honest "cost of this
#          process" number, since both bars map the same GTK
#   forks- process creations per second, system wide

sample_secs=${1:-10}

pids=""
for p in $(pgrep -x eww) $(pgrep -f 'taskbar\.sh') $(pgrep -f 'config[.]py'); do
    pids="$pids $p"
done

[ -z "$pids" ] && echo "no bar running" && exit 1

hz=$(getconf CLK_TCK)
f1=$(awk '/^processes/{print $2}' /proc/stat)

rss_total=0
pss_total=0
for p in $pids; do
    rss=$(awk '/^Rss:/{s+=$2}END{print s+0}' /proc/$p/smaps_rollup 2>/dev/null)
    pss=$(awk '/^Pss:/{s+=$2}END{print s+0}' /proc/$p/smaps_rollup 2>/dev/null)
    eval "t_$p=$(awk '{print $14+$15}' /proc/$p/stat 2>/dev/null)"
    rss_total=$((rss_total + rss))
    pss_total=$((pss_total + pss))
    printf '  pid %-7s rss %6s kB  pss %6s kB  %s\n' \
        "$p" "$rss" "$pss" "$(ps -o comm= -p $p)"
done

sleep "$sample_secs"

f2=$(awk '/^processes/{print $2}' /proc/stat)

cpu_total=0
for p in $pids; do
    eval "old=\$t_$p"
    new=$(awk '{print $14+$15}' /proc/$p/stat 2>/dev/null)
    cpu_total=$((cpu_total + new - old))
done

echo
printf 'total rss   %s kB (%s MB)\n' "$rss_total" "$((rss_total / 1024))"
printf 'total pss   %s kB (%s MB)\n' "$pss_total" "$((pss_total / 1024))"
awk -v c=$cpu_total -v hz=$hz -v s=$sample_secs \
    'BEGIN{printf "cpu         %.1f%% of one core\n", c/hz/s*100}'
awk -v a=$f1 -v b=$f2 -v s=$sample_secs \
    'BEGIN{printf "forks       %.0f/sec system wide\n", (b-a)/s}'
