#!/usr/bin/python3

import argparse
import json
import os
import pprint
import re
import sys

from typing import Dict, List, Optional, Tuple, Union

PATTERN = re.compile("%{_libdir}/(lib)?[a-zA-Z0-9]*\*[.]?so[.]?\*")

if (sys.version_info.major == 3) and (sys.version_info.minor < 6):
    print("python 3.6 or later is required to run this script.")
    exit(1)


def main():
    arguments = get_arguments()

    specs = get_specs(arguments["directory"])
    affected, report = analyze_specs(specs)

    if arguments["print"]:
        print_report(report)

    if arguments["report"]:
        write_report(report)

    print()
    print(f"Number of packages using globs for shared libraries: {affected}")
    print()


def get_arguments() -> dict:
    """This function returns a dictionary containing the parsed command line arguments."""

    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument("directory", action="store", nargs="?", default=".",
                            help="path of directory containing .spec files (defaults to '.')")
    cli_parser.add_argument("--report", action="store_const", const=True, default=False,
                            help="enable generating 'report.json'")
    cli_parser.add_argument("--no-print", action="store_const", const=False, default=True,
                            help="disable printing report to standard output", dest="print")

    arguments = vars(cli_parser.parse_args())
    return arguments


def print_report(report):
    pprint.pprint(report)


def write_report(report):
    with open("report.json", "w") as f:
        f.write(json.dumps(report, indent=2, sort_keys=True))


def get_specs(directory: str) -> List[str]:
    """This function returns the list of .spec files with were found in the specified directory."""
    files = os.listdir(directory)
    specs = filter((lambda file: file.endswith(".spec")), files)
    paths = list(os.path.join(directory, spec) for spec in specs)

    paths.sort()
    return paths


def analyze_specs(paths: List[str]) -> Tuple[int,
                                             Dict[str, List[Dict[str, Union[int, str]]]]]:
    affected = 0
    report = dict()

    for path in paths:
        result = analyze_spec(path)

        if result is None:
            continue

        affected += 1
        package, statistics = result

        report[package] = statistics

    return affected, report


def analyze_spec(path: str) -> Optional[Tuple[str, List[Dict[str, Union[int, str]]]]]:
    lines = get_spec_lines(path)

    matches = list()

    for lineno, line in enumerate(lines):
        match = PATTERN.match(line)
        if match is not None:
            matches.append((lineno, line))

    if matches:
        package = os.path.splitext(os.path.basename(path))[0]
        statistics = list({"line": lineno, "string": line} for lineno, line in matches)
        return package, statistics

    else:
        return None


def get_spec_lines(path: str) -> List[str]:
    contents = get_file_content(path)
    lines = contents.split("\n")

    return lines


def get_file_content(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


if __name__ == "__main__":
    main()
