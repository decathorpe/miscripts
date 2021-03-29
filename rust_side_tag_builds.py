#!/usr/bin/python3

import argparse
import subprocess
import textwrap
from typing import List, Optional

import koji
import parse

SIDE_TAG_PARSER = parse.Parser("Side tag '{tag}' (id {id}) created.")


def koji_session() -> koji.ClientSession:
    module = koji.get_profile_module("koji")
    session_opts = koji.grab_session_options(module.config)
    session = koji.ClientSession(module.config.server, session_opts)
    return session


def list_buildroot(session: koji.ClientSession, nvr: str) -> List[str]:
    build = session.getBuild(nvr, strict=True)

    if build["state"] != koji.BUILD_STATES["COMPLETE"]:
        raise Exception("Build is not yet complete.")

    task = session.listTasks(
        opts={
            "method": "buildArch",
            "parent": build["task_id"],
        },
        queryOpts={"limit": 1}
    )[0]

    buildroot = session.listBuildroots(
        taskID=task["id"],
        queryOpts={"order": "-id", "limit": 1}
    )[0]

    rpms = session.listRPMs(componentBuildrootID=buildroot["id"])

    with session.multicall(strict=True) as multi:
        srpms = [
            multi.listRPMs(
                buildID=rpm['build_id'],
                arches='src',
                queryOpts={'limit': 1}
            )
            for rpm in rpms
            if rpm['name'].startswith('rust-') and rpm['name'].endswith('-devel')
        ]

    nvrs = set(data.result[0]['nvr'] for data in srpms)
    return [*sorted(nvrs)]


def nvr_to_name(nvr: str) -> str:
    return nvr.rsplit("-", 2)[0]


def fedpkg_switch_branch(branch: str):
    ret = subprocess.run(["fedpkg", "switch-branch", branch])
    ret.check_returncode()


def fedpkg_request_side_tag(branch: str) -> str:
    ret = subprocess.run(["fedpkg", "request-side-tag"], stdout=subprocess.PIPE)
    ret.check_returncode()
    side_tag_output = ret.stdout.decode()

    try:
        parsed = SIDE_TAG_PARSER.parse(side_tag_output.split("\n")[0])
        tag = parsed.named["tag"]
        yde = parsed.named["id"]
        assert f"{branch}-build-side-{yde}" == tag
    except:
        print("Unable to parse name of side tag from fedpkg output.")
        print(side_tag_output)
        tag = input("Please enter enter the tag name manually: ")

    return tag


def koji_wait_repo(tag, build: Optional[str] = None):
    if build is None:
        ret = subprocess.run(["koji", "wait-repo", tag])
        ret.check_returncode()
    else:
        ret = subprocess.run(["koji", "wait-repo", tag, "--build", build])
        ret.check_returncode()


def koji_add_pkg(tag: str, packages: List[str]):
    ret = subprocess.run(["koji", "add-pkg", "--owner", "releng", tag, "--force"] + packages)
    ret.check_returncode()


def koji_tag_build(tag: str, builds: List[str]):
    ret = subprocess.run(["koji", "tag-build", tag] + builds)
    ret.check_returncode()


def fedpkg_build(target: str):
    ret = subprocess.run(["fedpkg", "build", "--target", target])
    ret.check_returncode()


def koji_untag_build(tag: str, builds: List[str]):
    ret = subprocess.run(["koji", "untag-build", tag] + builds)
    ret.check_returncode()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""\
        This script automatically builds Rust binary packages for fedora 31 - 33.
        Run this script from within the dist-git repository where you have
        prepared *and pushed* branches with the changes you want to build."""),
    )
    parser.add_argument("rawhide_build", help="NVR of the rawhide build")
    parser.add_argument("branch", nargs="+", help="names of dist-git branch(es), e.g. f32")
    args = parser.parse_args()

    session = koji_session()

    pkg = nvr_to_name(args.rawhide_build)
    buildroot = list_buildroot(session, args.rawhide_build)
    buildroot_pkgs = [nvr_to_name(nvr) for nvr in buildroot if nvr.startswith("rust-")]

    side_tags: List[str] = []

    for branch in args.branch:
        fedpkg_switch_branch(branch)

        tag = fedpkg_request_side_tag(branch)
        side_tags.append(tag)

        koji_wait_repo(tag)

        koji_add_pkg(tag, buildroot_pkgs + [pkg])

        koji_tag_build(tag, buildroot)

        for build in buildroot:
            koji_wait_repo(tag, build)

        fedpkg_build(tag)

        koji_untag_build(tag, buildroot)

    print("Builds finished. Now create bodhi updates for the following side tags:")
    for tag in side_tags:
        print(f" - {tag}")

    return 0


if __name__ == "__main__":
    exit(main())
