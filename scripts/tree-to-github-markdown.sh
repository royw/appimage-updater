#!/usr/bin/env bash

#File: tree2githubmd
#Description: Convert output of unix tree utility to Github flavoured Markdown

tree=$(tree --charset ascii "$@" |
sed -e 's/| \+/  /g' -e 's/[|`]-\+/ -/g' -e 's/^ //' -e '1 a\\')
printf "**Code/Directory Structure:**\n\n${tree}\n"
