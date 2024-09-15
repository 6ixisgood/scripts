#!/bin/bash

LINE=$(xinput | grep "$1")
ID=$(echo "$LINE" | cut -f 2 | tr 'id=' ' ')
STATUS==$(echo "$LINE" | cut -f 3)

if [[ $STATUS  == '=[floating slave]' ]]; then
	xinput enable $ID
else
	xinput disable $ID
fi
