#!/usr/bin/python3

# PYTHON_ARGCOMPLETE_OK

import argparse
import os
import subprocess
import tempfile
from collections import OrderedDict
from urllib.parse import urlparse

import requests
import rpm

HELP_TEXT = """\
Spectool is a tool to expand and download sources and patches from specfiles.

If you experience problems with specific specfiles, try to run

  rpmbuild --nobuild --nodeps <specfile>

on the file which might give a clue why spectool fails on a file (ignore
anything about missing sources or patches). The plan is to catch errors like
this in spectool itself and warn the user about it in the future."""


def complete_spec_paths(prefix, **kwargs):
    import glob

    return glob.glob(prefix + "*.spec")


def get_args() -> dict:
    try:
        import argcomplete
    except ImportError:
        argcomplete = None

    parser = argparse.ArgumentParser(
        description=HELP_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    ops = parser.add_argument_group("Operating mode")

    ops.add_argument(
        "--list-files",
        "--lf",
        "-l",
        action="store_const",
        const=True,
        default=True,
        help="lists the expanded sources/patches (default)",
    )

    ops.add_argument(
        "--get-files",
        "--gf",
        "-g",
        action="store_const",
        const=True,
        default=False,
        help="gets the sources/patches that are listed with a URL",
    )

    files = parser.add_argument_group("Files on which to operate")

    files.add_argument(
        "--all",
        "-a",
        action="store_const",
        const=True,
        default=True,
        help="all files, sources and patches (default)",
    )

    files.add_argument(
        "--sources",
        "-S",
        action="store_const",
        const=True,
        default=False,
        help="all sources",
    )

    files.add_argument(
        "--patches",
        "-P",
        action="store_const",
        const=True,
        default=False,
        help="all patches",
    )

    files.add_argument(
        "--source",
        "-s",
        action="store",
        help="specified sources",
    )

    files.add_argument(
        "--patch",
        "-p",
        action="store",
        help="specified patches",
    )

    misc = parser.add_argument_group("Miscellaneous")

    misc.add_argument(
        "--define",
        "-d",
        action="append",
        default=[],
        help="defines RPM macro 'macro' to be 'value'",
    )

    misc.add_argument(
        "--directory",
        "-C",
        action="store",
        default=None,
        help="download into specified directory (default '.')",
    )

    misc.add_argument(
        "--sourcedir",
        "-R",
        action="store_const",
        const=True,
        default=False,
        help="download into rpm's %%{_sourcedir}",
    )

    misc.add_argument(
        "--dry-run",
        "--dryrun",
        "-n",
        action="store_const",
        const=True,
        default=False,
        help="don't download anything, just show what would be done",
    )

    misc.add_argument(
        "--force",
        "-f",
        action="store_const",
        const=True,
        default=False,
        help="try to unlink and download if target files exist",
    )

    misc.add_argument(
        "--debug",
        "-D",
        action="store_const",
        const=True,
        default=False,
        help="output debug info, don't clean up when done",
    )

    specfile = parser.add_argument(
        "specfile",
        action="store",
    )

    if argcomplete:
        specfile.completer = complete_spec_paths

    if argcomplete:
        argcomplete.autocomplete(parser)

    return vars(parser.parse_args())


def split_numbers(args: str) -> list:
    return list(arg for arg in args.split(","))


def get_file(url: str, path: str, force: bool):
    if os.path.exists(path):
        if force:
            os.remove(path)
        else:
            print("File '{}' already present.".format(path))
            return

    response = requests.get(url)
    with open(path, "wb") as file:
        file.write(response.content)


class Spec:
    def __init__(self, path: str):
        self.path = path
        self.spec = rpm.spec(self.path)

        self.files = list(self.spec.sources)
        self.files.sort(key=(lambda file: file[1]))

        self._sources = None
        self._patches = None

    def _files(self, typ) -> OrderedDict:
        # file is a 3-tuple of (path, number, type)
        # type 1: source file
        # type 2: patch file
        files = OrderedDict()

        for file in self.files:
            if file[2] == typ:
                files[str(file[1])] = file[0]

        return files

    @property
    def sources(self) -> OrderedDict:
        if not self._sources:
            self._sources = self._files(1)

        return self._sources

    @property
    def patches(self) -> OrderedDict:
        if not self._patches:
            self._patches = self._files(2)

        return self._patches

    def print_source(self, number: int, value: str = None):
        if not value:
            value = self.sources[number]

        print("Source{}: {}".format(number, value))

    def print_patch(self, number: int, value: str = None):
        if not value:
            value = self.patches[number]

        print("Patch{}: {}".format(number, value))

    def list_sources(self):
        for (number, value) in self.sources.items():
            self.print_source(number, value)

    def list_patches(self):
        for (number, value) in self.patches.items():
            self.print_patch(number, value)

    @staticmethod
    def _get_file(value: str, directory: str, force: bool, dry: bool):
        parsed = urlparse(value)

        if "#" not in value:
            basename = os.path.basename(parsed.path)
        else:
            try:
                _, basename = value.split("#")
                basename = basename.lstrip("/")
            except ValueError:
                # multiple "#" characters inside
                print("Invalid URL:", value)
                return

        if parsed.scheme:
            if not dry:
                try:
                    print("Downloading: {}".format(value))
                    get_file(value, os.path.join(directory, basename), force)
                    print("Downloaded: {}".format(basename))
                except IOError as e:
                    print("Download failed:")
                    print(e)
            else:
                print("Would have downloaded: {}".format(value))

    def get_source(self, number: int, directory: str, force: bool, dry: bool, value: str = None):
        if not value:
            value = self.sources[number]

        self._get_file(value, directory, force, dry)

    def get_patch(self, number: int, directory: str, force: bool, dry: bool, value: str = None):
        if not value:
            value = self.patches[number]

        self._get_file(value, directory, force, dry)

    def get_sources(self, directory: str, force: bool, dry: bool):
        for number, value in self.sources.items():
            self.get_source(number, directory, force, dry, value)

    def get_patches(self, directory: str, force: bool, dry: bool):
        for number, value in self.patches.items():
            self.get_patch(number, directory, force, dry, value)


def main() -> int:
    args = get_args()

    if args["all"]:
        args["sources"] = True
        args["patches"] = True

    if args["debug"]:
        import pprint
        print("Parsed command line arguments:")
        pprint.pprint(args)

    path = args["specfile"]

    if not os.path.exists(path):
        print("The specified path doesn't exist.")
        return 1

    if not os.access(path, os.R_OK):
        print("The specified file can't be read.")
        return 1

    if args["define"]:
        defines = OrderedDict()

        for define in (arg.split(" ", 1) for arg in args["define"]):
            defines[define[0]] = define[1]

        temp = tempfile.NamedTemporaryFile("w", delete=False)

        for key, value in defines.items():
            temp.write("%global {} {}\n".format(key, value))

        with open(path, "r") as orig:
            temp.write(orig.read())

        temp.close()

        spec = Spec(temp.name)
        os.remove(temp.name)

    else:
        spec = Spec(path)

    if args["list_files"] and not args["get_files"]:
        if args["source"]:
            numbers = split_numbers(args["source"])

            for number in numbers:
                if number not in spec.sources.keys():
                    print("No source with number '{}' found.".format(number))
                    continue

                spec.print_source(number)

        elif args["sources"] and not args["patch"]:
            spec.list_sources()

        if args["patch"]:
            numbers = split_numbers(args["patch"])

            for number in numbers:
                if number not in spec.patches.keys():
                    print("No patch with number '{}' found.".format(number))
                    continue

                spec.print_patch(number)

        elif args["patches"] and not args["source"]:
            spec.list_patches()

    if args["get_files"]:
        force = args["force"]
        dry = args["dry_run"]

        if args["directory"] and args["sourcedir"]:
            print("Conflicting requests for download directory.")
            return 1

        if args["directory"]:
            directory = args["directory"]
        elif args["sourcedir"]:
            ret = subprocess.run(["rpm", "--eval", "%{_sourcedir}"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            ret.check_returncode()
            directory = ret.stdout.decode().strip()
        else:
            directory = os.getcwd()

        if args["source"]:
            numbers = split_numbers(args["source"])

            for number in numbers:
                if number not in spec.sources.keys():
                    print("No patch with number '{}' found.".format(number))
                    continue

                spec.get_source(number, directory, force, dry)

        elif args["sources"] and not args["patch"]:
            spec.get_sources(directory, force, dry)

        if args["patch"]:
            numbers = split_numbers(args["patch"])

            for number in numbers:
                if number not in spec.patches.keys():
                    print("No patch with number '{}' found.".format(number))
                    continue

                spec.get_patch(number, directory, force, dry)

        elif args["patches"] and not args["source"]:
            spec.get_patches(directory, force, dry)

    return 0


if __name__ == "__main__":
    exit(main())
