#!/bin/bash

DEVICES=$


function toggle() {
	local status=$(xinput list-props "$1" | grep "Device Enabled" | awk '{print $4}')

	if [[ $status == 1 ]]; then
		echo "Disabling $id"
		xinput disable $id
	else
		echo "Enabling $id"
		xinput enable $id
	fi
}

if [ $# -lt 1 ]; then
    echo "Usage: $0 <device_1> [device_2] [...]"
    exit 1
fi

for device in "$@"; do
	id=$(xinput | grep "$device" | cut -f2 | cut -d= -f2)
    toggle "$id"
done