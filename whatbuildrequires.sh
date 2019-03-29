#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "No argument given!"
    exit 1
fi

if [ -z "$2" ]; then
    echo "No argument given! Assuming rawhide."
    dist="rawhide"
    repos="--enablerepo=fedora-source"
else
    dist="$2"
    if [ "$2" == "rawhide" ]; then
        repos="--enablerepo=fedora-source"
    else
        repos="--enablerepo=fedora-source --enablerepo=updates-source --enablerepo=updates-testing-source"
    fi
fi

sudo dnf repoquery \
    --quiet \
    --releasever=$dist \
    --refresh \
    --disablerepo='*' \
    $repos \
    --alldeps \
    --archlist=src \
    --whatrequires "$1"

