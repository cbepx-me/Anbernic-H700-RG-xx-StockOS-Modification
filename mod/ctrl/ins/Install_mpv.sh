#!/bin/bash

progdir="$(cd $(dirname "$0"); pwd)"

cp -f "$progdir"/mpv_ins/mpv /usr/bin/mpv && chmod 777 /usr/bin/mpv
for file in "$progdir"/mpv_ins/lib*
do
    cp -f "${file}" /usr/lib/ && chmod 777 /usr/lib/${file##*/}
done
ln -fs /usr/lib/libmali.so.0.20.0 /usr/lib/libmali.so.1
sync
exit 0
