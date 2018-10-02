#!/bin/bash

# if metadata directory does not exist, create it
if [ ! -d $2 ]; then
    mkdir -p $2
fi

# move metadata from source to target
find $1 -regex '.*\.\(wpi\|wpp\|mrf\|mlf\|mes\|xml\)' -exec cp -v -n -t $2 {} +
find $1 -name SC* -exec cp -v -n -t $2 {} +
find $1 -name DC* -exec cp -v -n -t $2 {} +
