#!/usr/bin/env bash

USERNAME=$1

if [[ -n "USERNAME" ]]; then
    cd logs/${USERNAME}
    tail -n 1000 -f ${USERNAME}-*
fi