#!/bin/bash

progdir="$(cd $(dirname "$0") || exit; pwd)"/img_browser

export PYSDL2_DLL_PATH="/usr/lib"

program="python3 ${progdir}/main.py"
log_file="${progdir}/log.txt"
[ -f /mnt/mod/ctrl/volumeCtrl.dge ] && /mnt/mod/ctrl/volumeCtrl.dge &

$program > "$log_file" 2>&1

kill -9 $(pidof volumeCtrl.dge)
