#!/bin/bash

progdir="$(cd $(dirname "$0") || exit; pwd)"/themes_ins

export PYSDL2_DLL_PATH="/usr/lib"

[ ! -f /usr/bin/zip ] && cp -f "$progdir"/zip /usr/bin && chmod 777 /usr/bin/zip
[ ! -f /usr/bin/unzip ] && cp -f "$progdir"/unzip /usr/bin && chmod 777 /usr/bin/unzip

program="python3 ${progdir}/main.py"
log_file="${progdir}/log.txt"
[ -f /mnt/mod/ctrl/volumeCtrl.dge ] && /mnt/mod/ctrl/volumeCtrl.dge &

$program > "$log_file" 2>&1

kill -9 $(pidof volumeCtrl.dge)
