#!/bin/bash

progdir="$(cd $(dirname "$0"); pwd)"

cp -f "$progdir"/evtest_ins/evtest /mnt/vendor/bin/evtest && chmod 777 /mnt/vendor/bin/evtest
cp -f "$progdir"/evtest_ins/evtest /usr/bin/evtest && chmod 777 /usr/bin/evtest
sync
exit 0
