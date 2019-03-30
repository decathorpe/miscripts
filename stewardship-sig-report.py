#!/usr/bin/python3

import datetime

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

</body>
</html>
"""


def main() -> int:
    # populate "members" list
    sig = requests.get("https://src.fedoraproject.org/api/0/group/stewardship-sig?projects=true")

    json = sig.json()

    members = json["members"]
    members.sort()

    projects = json["projects"]

    # populate "maintained" table
    maintained = prettytable.PrettyTable()

    maintained.field_names = ["Package", "Main Admin", "Admin", "Commit"]
    num_maintained = 0

    for project in projects:
        name = project["name"]
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

    template = jinja2.Template(TEMPLATE)
    out = template.render(
        current_date=datetime.datetime.utcnow().isoformat() + " (UTC)",
        num_members=len(members),
        members=members,
        num_maintained=num_maintained,
        table=maintained.get_html_string(),
    )

    print(out)

    return 0


if __name__ == "__main__":
    exit(main())

