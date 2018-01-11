#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, json, time
import requests

data = []
logos = {}

re_format_date = re.compile(r"(..)/(..)/(....) (..:..:..)")
def reformat_date(obj, field):
    obj[field] = re_format_date.sub(r"\3-\2-\1T\4", obj[field])

def safe_dl(url, fail=False, retry=5):
    try:
        return requests.get(url).json()
    except Exception as e:
        if retry:
            time.sleep(1)
            return safe_dl(url, fail=fail, retry=retry-1)
        print "ERROR reading %s. %s: %s" % (url, type(e), e)
        if fail:
            exit(1)
        return None

for org in safe_dl("http://www.hatvp.fr/agora/stock.json", True):
    org["url_json"] = "http://www.hatvp.fr/agora/%s.json" % org["identifiantNational"]
    reformat_date(org, "datePremierePublication")
    details = safe_dl(org["url_json"])
    if details:
        reformat_date(details["publicationCourante"], "dateCreation")
        [reformat_date(h, "dateCreation") for h in details["historique"]]
        org.update(details["publicationCourante"])
        historique = [h for h in details["historique"] if h["dateCreation"] != org["dateCreation"]]
        org["historique"] = sorted(historique, key=lambda x: x["dateCreation"])
        if "logo" in details:
            logos[org["identifiantNational"]] = {
              "data": details["logo"],
              "type": details["logoType"]
            }
    data.append(org)

data = sorted(data, key=lambda x: x["denomination"])

with open(os.path.join("data", "registre-lobbying-HATVP.json"), "w") as f:
    print >> f, json.dumps(data, f, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
with open(os.path.join("data", "registre-lobbying-HATVP-logos.json"), "w") as f:
    json.dump(logos, f, indent=1, sort_keys=True)
