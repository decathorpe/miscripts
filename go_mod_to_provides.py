#!/usr/bin/python3

import os
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print("No file given.")
        return 1

    path = sys.argv[1]

    if not os.path.exists(path):
        print("File not found.")
        return 1

    if not os.access(path, os.R_OK):
        print("File could not be read.")
        return 1

    with open(path) as file:
        contents = file.read()

    lines = contents.split("\n")

    # requirements are indented with a tabstopp
    requires = list(filter(lambda line: line.startswith("\t"), lines))

    provides = list()

    for require in requires:
        info = require.strip().split(" ")

        # normal dependency: name version
        if len(info) == 2:
            name, version = info

        # indirect dependency: name version // indirect
        elif len(info) == 4:
            name, version, _, _ = info

        # something else: ignore
        else:
            print("Unexpected line encountered:")
            print(require)
            continue

        # snapshot version info: only use git hash (12 chars)
        if len(version) > 28:
            version = version[-12:]

        # v-prefixed stable version
        else:
            version = version.lstrip("v")

        provides.append((name, version))

    for name, version in provides:
        print(f"Provides:       bundled(golang({name})) = {version}")


if __name__ == "__main__":
    exit(main())
