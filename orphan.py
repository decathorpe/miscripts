#!/usr/bin/python3

from enum import StrEnum

import requests

API_TOKEN = ""

class OrphanReason(StrEnum):
    LackOfTime = "Lack of time"
    DoNotUseIt = "Do not use it anymore"
    Unmaintained = "Unmaintained upstream"
    FailsToBuild = "Fails to build from source"
    NotFixed = "Important bug not fixed"
    OrphanedByReleng = "Orphaned by releng"
    Other = "Other"

def orphan(package: str, reason: OrphanReason, reason_info: str):
    url = f"https://src.fedoraproject.org/_dg/orphan/rpms/{package}"
    data = {"orphan_reason": str(reason), "orphan_reason_info": reason_info}
    headers = {"Authorization": f"token {API_TOKEN}"}
    ret = requests.post(url, json=data, headers=headers)
    ret.raise_for_status()

packages = []

for package in packages:    
    orphan(package, OrphanReason.DoNotUseIt, "")

