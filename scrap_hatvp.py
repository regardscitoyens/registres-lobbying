#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, json
import requests

data = []
logos = {}

re_format_date = re.compile(r"(..)/(..)/(....) (..:..:..)")
def reformat_date(obj, field):
    obj[field] = re_format_date.sub(r"\3-\2-\1T\4", obj[field])

for org in requests.get("http://www.hatvp.fr/agora/stock.json").json():
    org["url_json"] = "http://www.hatvp.fr/agora/%s.json" % org["identifiantNational"]
    reformat_date(org, "datePremierePublication")
    details = requests.get(org["url_json"]).json()
    reformat_date(details["publicationCourante"], "dateCreation")
    [reformat_date(h, "dateCreation") for h in details["historique"]]
    org.update(details["publicationCourante"])
    historique = [h for h in details["historique"] if h["dateCreation"] != org["dateCreation"]]
    org["historique"] = sorted(historique, key=lambda x: x["dateCreation"])
    data.append(org)
    if "logo" in details:
        logos[org["identifiantNational"]] = {
          "data": details["logo"],
          "type": details["logoType"]
        }

data = sorted(data, key=lambda x: x["denomination"])

with open(os.path.join("data", "registre-lobbying-HATVP.json"), "w") as f:
    print >> f, json.dumps(data, f, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
with open(os.path.join("data", "registre-lobbying-HATVP-logos.json"), "w") as f:
    json.dump(logos, f, indent=1, sort_keys=True)
