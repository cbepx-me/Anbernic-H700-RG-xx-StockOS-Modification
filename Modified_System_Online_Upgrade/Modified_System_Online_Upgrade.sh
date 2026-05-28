#!/bin/bash

version="1.0.0"
progdir="$(cd $(dirname "$0") || exit; pwd)"
program="${progdir}/upgrade/launcher.py"
log_file="${progdir}/upgrade/log.txt"
SCRIPT_NAME="$0"
NEW_FILE="$progdir/upgrade/update.sh"
APP_FILE="/tmp/app.tar.gz"

pkill -f "launcher.py" 2>/dev/null || true

export PYSDL2_DLL_PATH="/usr/lib"

while true
do
    if [ -f "$NEW_FILE" ]; then
        chmod +x "$NEW_FILE"
        if bash -n "$NEW_FILE" 2>/dev/null; then
            cat "$NEW_FILE" > "$SCRIPT_NAME"
            rm -f "$NEW_FILE"
            exec "$SCRIPT_NAME" "$@"
        else
            echo "The new version has syntax errors and the update has been aborted"
            rm -f "$NEW_FILE"
        fi
    elif [ -f "$APP_FILE" ]; then
        sleep 5
        tar -xf "$APP_FILE" -C "$progdir/"
        [ -f "$APP_FILE" ] && rm -rf "$APP_FILE"
    else
        [ -f /mnt/mod/ctrl/volumeCtrl.dge ] && /mnt/mod/ctrl/volumeCtrl.dge &
        sleep 1
        $program > $log_file 2>&1
        if [ $? -ne 36 ]; then
            break
        fi
        kill -9 $(pidof volumeCtrl.dge)
        sleep 1
    fi
done
kill -9 $(pidof volumeCtrl.dge)
exit 0