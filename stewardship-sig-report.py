#!/usr/bin/python3

import argparse
import datetime
import subprocess

import jinja2
import requests
import prettytable


TEMPLATE = """\
<html>

<head>
<title>
Stewardship SIG Status Page
</title>
</head>

<body>

<h1>
Stewardship SIG Status Page
</h1>

<p2>
Rendered last at: {{ current_date }}
</p2>

<h2>
Current members ({{ num_members }})
</h2>

<ul>
{% for member in members %}
<li>{{ member }}</li>
{% endfor %}
</ul>

<h2>
Maintained packages ({{ num_maintained }})
</h2>

{{ table }}


<h2>
Leaf Packages (double check this)
</h2>

<ul>
{% for package in leaves %}
<li>{{ package }}</li>
{% endfor %}
</ul>

<h2>
Package dependencies
</h2>

{% for package in packages %}

<h3>
{{ package.name }}
</h3>

<ul>
{% for dependency in package.reqs %}
<li>Required-By: {{ dependency }}</li>
{% endfor %}

{% for dependency in package.brs %}
<li>BuildRequired-By: {{ dependency }}</li>
{% endfor %}
</ul>
{% endfor %}

</body>
</html>
"""


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


def main() -> int:
    print()

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", action="store")
    args = vars(parser.parse_args())

    output = args["output"]

    # populate "members" list
    print("Getting group information from https://src.fedoraproject.org ...")
    sig = requests.get("https://src.fedoraproject.org/api/0/group/stewardship-sig?projects=true")

    json = sig.json()

    members = json["members"]
    members.sort()

    projects = json["projects"]

    # populate "maintained" table
    print("Populating package table ...")
    maintained = prettytable.PrettyTable()

    maintained.field_names = ["Package", "Main Admin", "Admin", "Commit"]
    num_maintained = 0

    package_names = []
    for project in projects:
        name = project["name"]
        package_names.append(name)

        users = project["access_users"]

        owner = users["owner"]
        admin = users["admin"]
        commit = users["commit"]

        admin.sort()
        commit.sort()

        maintained.add_row([
            name,
            ", ".join(owner),
            ", ".join(admin) if admin else "--",
            ", ".join(commit) if commit else "--"
        ])

        num_maintained += 1

    maintained.hrules = prettytable.HEADER
    maintained.vrules = prettytable.NONE

    maintained.header = True
    maintained.align = "l"

    # check package dependencies
    print("Populating package dependency information ...")

    packages = []
    leaves = []

    for package in package_names:
        print(" -", package)
        reqs, brs = get_requires(package)

        if (len(reqs) == 0) and (len(brs) == 0):
            leaves.append(package)
        else:
            packages.append({"name": package, "reqs": reqs, "brs": brs})

    # render output
    print("Rendering output ...")
    template = jinja2.Template(TEMPLATE)
    out = template.render(
        current_date=datetime.datetime.utcnow().isoformat() + " (UTC)",
        num_members=len(members),
        members=members,
        num_maintained=num_maintained,
        table=maintained.get_html_string(),
        leaves=leaves,
        packages=packages,
    )

    # write output to file
    with open(output, "w") as file:
        file.write(out)

    return 0


if __name__ == "__main__":
    exit(main())

