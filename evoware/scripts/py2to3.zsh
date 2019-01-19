#!/bin/bash

echo "USAGE: "
echo "py2to3.zsh module.py"
echo "Run from package folder evowarepy/evoware"
echo "This will change the file in-place and then try to run a graphical diff"
echo "against a copy in another folder (given as second argument)"

OLDPATH="../../evowarepy2x/evoware"

exists() { type -t "$1" > /dev/null 2>&1; }

2to3 -n -W $1

if exists meld; then
    meld $1 $OLDPATH/$1
elif exists bcomp; then
    bcomp $1 $OLDPATH/$1
fi
