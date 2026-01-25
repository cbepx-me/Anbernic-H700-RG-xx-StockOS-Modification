#!/bin/bash

progdir="$(cd $(dirname "$0") || exit; pwd)"
SOU_DIR="${progdir%/*}"
program="python3 ${progdir}/mod/main.py"
log_file="${progdir}/update.log"
export PYSDL2_DLL_PATH="/usr/lib"
$program > "$log_file" 2>&1

if [ -f "$progdir/reboot.flg" ]; then
    rm -f "$progdir/reboot.flg"
    if [[ "$SOU_DIR" != "/mnt/mod" ]]; then
        rm -rf "$progdir"
    fi
    sync
    reboot
    while true;do sleep 5; done
fi
