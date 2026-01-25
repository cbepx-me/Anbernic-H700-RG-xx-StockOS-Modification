#!/bin/bash

progdir="$(cd $(dirname "$0"); pwd)"
[ -f /usr/sbin/gdisk ] && exit 1
dpkg -i "$progdir"/gdisk_ins/*.deb
sync
exit 0
