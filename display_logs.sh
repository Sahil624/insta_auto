#!/usr/bin/env bash

if [[ $# -eq 0 ]]; then
    echo "Please give username as an argument"
    exit 1
fi

USERNAME=$1

if [[ -n "USERNAME" ]]; then
    cd logs/${USERNAME}
    tail -n 1000 -f ${USERNAME}-*
fi