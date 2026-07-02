#!/bin/dash

conf=/home/$USER/.config/eww

git clone https://github.com/siduck/zuup $conf

mkdir $conf/cache
mkdir $conf/cache/multi_win
mkdir $conf/cache/multi_winames

touch $conf/cache/refresh_dock

echo [] > $conf/cache/pinned_apps
