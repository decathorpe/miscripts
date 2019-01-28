#!/usr/bin/python3

# Markdown formatter (primarily for tables)
# Copyright (C) 2018 Fabio Valentini <decathorpe@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

"""
This python module / script takes an unformatted markdown string and returns a
string where all tables have aligned column separators.
"""

from collections import OrderedDict

MIN_SEP_LENGTH = 3


def is_separator(string: str) -> bool:
    """This function returns true if the string is a valid header separator."""
    for char in string:
        if char != "-":
            return False
    else:
        if len(string) >= MIN_SEP_LENGTH:
            return True
        else:
            return False


def fmt_table(lines: list) -> list:
    table = list([] for _ in range(len(lines)))
    lengths = OrderedDict()

    for (j, line) in enumerate(lines):
        cells = line.lstrip("|").rstrip("|").split("|")
        for (k, cell) in enumerate(cells):
            content = cell.lstrip(" ").rstrip(" ")
            table[j].append(content)
            if k not in lengths:
                lengths[k] = list()
            if not is_separator(content):
                lengths[k].append(len(content))
            else:
                lengths[k].append(MIN_SEP_LENGTH)

    max_lengths = OrderedDict()
    for row in lengths:
        max_lengths[row] = max(lengths[row])

    output = list()
    for row_no in enumerate(table):
        i, row = row_no
        output.append(list())
        for cell_no in enumerate(row):
            j, cell = cell_no
            if is_separator(cell):
                contents = " " + max_lengths[j] * "-" + " "
            else:
                contents = " " + cell + (max_lengths[j] - len(cell)) * " " + " "
            output[i].append(contents)

    rows = list("|" + "|".join(line) + "|" for line in output)

    return rows


def fmt(string: str) -> str:
    """
    This function takes a string containing an unformatted markdown string as
    input, and returns a string with formatted markdown, with column separators
    in tables aligned prettily.
    """

    lines = string.split("\n")
    
    # set up output buffer
    output_lines = list()

    # set up table buffer and state tracking
    table_lines = list()
    parsing_table = False

    for line in lines:
        # If, during the parsing of a table,
        if parsing_table:

            # an empty line is read:
            # all lines of the table have been read.
            if line == "":
                # - extend the output by the formatted table
                output_lines.extend(fmt_table(table_lines))
                # - extend the output by the just read empty line
                output_lines.append("")
                # - clear the table buffer
                table_lines.clear()
                # - set that no table is being parsed anymore
                parsing_table = False

            # a line containing a table row is read:
            # a new row will be added to the table buffer
            elif line[0] == "|":
                # - add the new row to the table buffer
                table_lines.append(line)

            # a non-empty, non-table line is read:
            # all lines of the table have been read.
            else:
                # - extend the output by the formatted table
                output_lines.extend(fmt_table(table_lines))
                # - extend the output by the just read non-empty line
                output_lines.extend(line)
                # - clear the table buffer
                table_lines.clear()
                # - set that no table is being parsed anymore
                parsing_table = False

        # If, during the parsing of a markdown file,
        else:

            # an empty line is read:
            # just append the empty line to the output buffer.
            if line == "":
                output_lines.append(line)

            # a table row is read:
            # - start parsing a table
            # - add row to the table buffer
            elif line[0] == "|":
                parsing_table = True
                table_lines.append(line)

            # a non-empty, non-table line is read:
            # just append the line to the output buffer.
            else:
                output_lines.append(line)

    # If the table buffer is non-empty after parsing the file:
    # flush the table buffer to the output buffer.
    if parsing_table and table_lines:
        output_lines.extend(fmt_table(table_lines))

    # Format the output buffer into a nice string.
    string = "\n".join(output_lines)
    return string


def main():
    """
    This function is executed when the module is executed instead of imported.
    It reads one argument from the command line, which can be an input file
    name, or "-", if the input should be read from stdin.
    """

    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        "--inplace",
        help="overwrite input file",
        action="store_const",
        default=False,
        const=True)
    parser.add_argument(
        "input",
        help="path to input file (or '-' for stdin)",
        action="store")
    parser.add_argument(
        "output",
        help="path to output file (printing to stdout if omitted)",
        action="store",
        nargs="?")

    arguments = vars(parser.parse_args())

    input_path = arguments["input"]
    output_path = arguments["output"]
    inplace = arguments["inplace"]

    if input_path == "-":
        unformatted = sys.stdin.read()
    else:
        if not os.path.exists(input_path):
            print("File doesn't exist.")
            sys.exit(1)
        with open(input_path) as file:
            unformatted = file.read()

    formatted = fmt(unformatted)

    if inplace:
        if output_path is not None:
            print("Output path is ignored because '--inplace' ('-i') was supplied.")
        with open(os.path.basename(input_path), "w") as file:
            file.write(formatted)

    elif output_path is None:
        print(formatted)

    else:
        with open(output_path, "w") as file:
            file.write(formatted)


if __name__ == "__main__":
    main()

