#!/bin/bash

find ./ -name install.sh | sort -n | while read line; do
    rc=$(sudo ${line})
done
