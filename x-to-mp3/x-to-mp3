#!/bin/bash
find $1 -maxdepth 1 -regextype egrep -regex ".*(.wav|.mp4|.flac|.m4a)" \
	| xargs -I {} -n 1 sh -c \ 'export f="{}"; \
	ffmpeg -i "$f" -vn -codec:v copy \
	-codec:a libmp3lame -q:a 0 '"${2%/}"'/"$(basename "${f%.*}").mp3"' \;
	
