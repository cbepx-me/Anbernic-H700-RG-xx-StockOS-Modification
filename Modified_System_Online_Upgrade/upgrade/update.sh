#!/bin/bash

version="1.0.3"
progdir="$(cd $(dirname "$0") || exit; pwd)"
program="${progdir}/upgrade/main.py"
log_file="${progdir}/upgrade/log.txt"
SCRIPT_NAME="$0"
NEW_FILE="$progdir/upgrade/update.sh"
# Only verified producers/consumers participate in this protocol.
APP_UPDATE_PROTOCOL=2
APP_FILE="/tmp/anbernic-app-ready.tar.gz"
APP_MD5="/tmp/anbernic-app-ready.md5"

pkill -f "main.py" 2>/dev/null || true

export PYSDL2_DLL_PATH="/usr/lib"

while true
do
    if [ -f "$NEW_FILE" ]; then
        chmod +x "$NEW_FILE"
        if bash -n "$NEW_FILE" 2>/dev/null && grep -qx 'APP_UPDATE_PROTOCOL=2' "$NEW_FILE"; then
            cat "$NEW_FILE" > "$SCRIPT_NAME"
            rm -f "$NEW_FILE"
            exec "$SCRIPT_NAME" "$@"
        else
            echo "The new wrapper is invalid or lacks the verified-update protocol; keeping the current wrapper"
            rm -f "$NEW_FILE"
        fi
    elif [ -f "$APP_MD5" ]; then
        expected_md5=$(cat "$APP_MD5")
        actual_md5=$(md5sum "$APP_FILE" 2>/dev/null)
        actual_md5=${actual_md5%% *}
        # Consume readiness before extraction, including failed/stale markers.
        rm -f "$APP_MD5"
        if [[ "$expected_md5" =~ ^[[:xdigit:]]{32}$ ]] &&
           [ "${actual_md5,,}" = "${expected_md5,,}" ] &&
           tar -tf "$APP_FILE" >/dev/null 2>&1; then
            if ! tar -xf "$APP_FILE" -C "$progdir/"; then
                echo "Application update extraction failed"
            fi
        else
            echo "Ignoring unverified or invalid application update"
        fi
        rm -f "$APP_FILE"
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
[ -x /mnt/mmc/autostart ] && /mnt/mmc/autostart
kill -9 $(pidof volumeCtrl.dge)
exit 0