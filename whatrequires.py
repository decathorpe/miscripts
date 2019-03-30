#!/usr/bin/python3

import argparse
import subprocess


def get_requires(package, run_as_root=False):
    cmd = []

    if run_as_root:
        cmd.append("sudo")

    cmd.extend(["dnf", "--quiet", "repoquery",
                "--repo=rawhide", "--repo=rawhide-source"])

    cmd.extend(["--whatrequires", package])

    ret = subprocess.run(cmd, stdout=subprocess.PIPE)

    ret.check_returncode()

    output: str = ret.stdout.decode()

    deps = output.splitlines()

    requires = []
    buildrequires = []

    for dep in deps:
        # epoch, version, release aren't used yet
        (n, ev, ra) = dep.rsplit("-", 2)
        (e, v) = ev.split(":")
        (r, a) = ra.rsplit(".", 1)

        if a == "src":
            buildrequires.append(n)
        else:
            requires.append(n)

    requires.sort()
    buildrequires.sort()

    return requires, buildrequires


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", action="store")

    args = vars(parser.parse_args())
    package = args["package"]

    reqs, brs = get_requires(package)

    print()

    for req in reqs:
        print("Required-by:", req)

    print()

    for br in brs:
        print("BuildRequired-by:", br)

    print()

    return 0


if __name__ == "__main__":
    exit(main())
