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

app_package_compatible() {
    python3 "$progdir/upgrade/update_package.py" "$APP_FILE"
}

while true
do
    # Legacy downloads are unverified; orphan handoff files are never installable.
    rm -f /tmp/app.tar.gz /tmp/app.tar.gz.download.json /tmp/app.tar.gz.download.json.tmp \
          /tmp/app.tar.gz.part.download.json.tmp "$APP_MD5.tmp"
    if [ ! -f /tmp/app.tar.gz.part ]; then
        rm -f /tmp/app.tar.gz.part.download.json
    fi
    if [ ! -f "$APP_MD5" ]; then
        rm -f "$APP_FILE"
    fi
    if [ -f "$NEW_FILE" ]; then
        chmod +x "$NEW_FILE"
        if bash -n "$NEW_FILE" 2>/dev/null && grep -qx 'APP_UPDATE_PROTOCOL=2' "$NEW_FILE"; then
            staged_wrapper=$(mktemp "${SCRIPT_NAME}.XXXXXX")
            if [ -n "$staged_wrapper" ] &&
               cat "$NEW_FILE" > "$staged_wrapper" &&
               bash -n "$staged_wrapper" &&
               grep -qx 'APP_UPDATE_PROTOCOL=2' "$staged_wrapper" &&
               chmod 755 "$staged_wrapper" &&
               mv -f "$staged_wrapper" "$SCRIPT_NAME"; then
                rm -f "$NEW_FILE"
                exec "$SCRIPT_NAME" "$@"
            else
                rm -f "$staged_wrapper"
                echo "Wrapper replacement failed; keeping the installed wrapper"
                exit 1
            fi
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
           tar -tf "$APP_FILE" >/dev/null 2>&1 &&
           app_package_compatible; then
            if ! tar -xf "$APP_FILE" -C "$progdir/"; then
                echo "Application update extraction failed"
                rm -f "$APP_FILE"
                exit 1
            fi
        else
            echo "Rejecting unverified, invalid or incompatible application update"
            rm -f "$APP_FILE"
            exit 1
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