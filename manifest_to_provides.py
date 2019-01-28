#!/usr/bin/python3

import json
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
        try:
            raw = json.loads(file.read())
        except json.JSONDecodeError:
            print("Manifest file could not be parsed.")
            return 1

        if "dependencies" not in raw:
            print("Manifest file invalid.")
            return 1

        deps = raw["dependencies"]

        for dep in deps:
            try:
                print("Provides:       bundled(golang({})) = {}"
                      .format(dep["importpath"], dep["revision"]))
            except KeyError:
                print("Error parsing dependency '{}'.".format(dep))
                return 1
        return 0

if __name__ == "__main__":
    exit(main())

