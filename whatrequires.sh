#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "No argument given!"
    exit 1
fi

if [ -z "$2" ]; then
    echo "No argument given! Assuming rawhide."
    dist="rawhide"
    repos="--enablerepo=fedora"
else
    dist="$2"
    if [ "$2" == "rawhide" ]; then
        repos="--enablerepo=fedora"
    else
        repos="--enablerepo=fedora --enablerepo=updates --enablerepo=updates-testing"
    fi
fi

sudo dnf repoquery \
    --quiet \
    --releasever=$dist \
    --refresh \
    --disablerepo='*' \
    $repos \
    --whatrequires "$1"

