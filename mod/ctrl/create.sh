#!/bin/sh
#make by G.R.H

rm -f /mnt/.please_create
if [ -e "/dev/mmcblk0p8" ]; then
    exit 1
fi

DEVICE="/dev/mmcblk0"
PART1="/dev/mmcblk0p8"
PART_NUM=7

if [ ! -e ${PART1} ]; then
    SIZE="$(echo $(parted -m ${DEVICE} print all | awk 'BEGIN {FS=":"} /^'"${PART_NUM}"'/ {print $3}'))"
    parted -s -a optimal -m ${DEVICE} mkpart primary fat32 ${SIZE} 99%
    partprobe ${DEVICE}
    mkfs.vfat -n ROMS ${PART1}
    echo -e "v\nw" | fdisk ${DEVICE}
    echo -e "x\na\n1\n62\n63\n64\na\n2\n62\n63\n64\na\n3\n62\n63\n64\na\n4\n62\n63\n64\na\n5\n62\n63\n64\na\n6\n62\n63\n64\na\n7\n62\n63\n64\ne\nw\ny\n" | gdisk /dev/mmcblk0
    sync
    sleep 3
    reboot
    while true; do sleep 5; done
fi
exit 0
