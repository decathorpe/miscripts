#!/usr/bin/python3

import argparse
import datetime
import sys

from git import Repo

from git.exc import BadName
from git.exc import InvalidGitRepositoryError
from git.exc import NoSuchPathError


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "repo",
        help="specify repository path manually (default=.)",
        action="store",
        nargs="?",
        default=".")
    parser.add_argument(
        "ref",
        help="specify ref manually (default=master)",
        action="store",
        nargs="?",
        default="master")

    arguments = vars(parser.parse_args())
    return arguments

def main():
    arguments = get_arguments()

    ref = arguments["ref"]
    path = arguments["repo"]

    try:
        repo = Repo(path)
    except InvalidGitRepositoryError:
        print("The specified directory is not a valid git repository. Aborting.")
        return
    except NoSuchPathError:
        print("The specified directory does not exist. Aborting.")
        return

    try:
        commit = repo.commit(ref)
    except BadName:
        print("The specified ref is not valid. Aborting.")
        return

    commit_datetime = commit.committed_datetime.astimezone(
        datetime.timezone.utc)

    commit_datetime_str = datetime.datetime.strftime(
        commit_datetime, "%Y%m%d")

    print()
    print("ref '{}': committed date (format YYYYMMDD, UTC): {}".format(
        ref, commit_datetime_str))
    print()
    print("Use the following snippet in an RPM .spec file:")
    print()
    print("%global commit      {}".format(commit))
    print("%global shortcommit {}".format("%(c=%{commit}; echo ${c:0:7})"))
    print("%global commitdate  {}".format(commit_datetime_str))
    print()

if __name__ == "__main__":
    main()

