#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, json, time
import requests

imgpath = os.path.join("images", "logos-HATVP")
for d in ["data", "images", imgpath]:
    if not os.path.exists(d):
        os.makedirs(d)

imgfmt = lambda f: "png" if "png" in f else "jpg"

data = []
done = {}
actions = {}

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

hatvp = safe_dl("https://www.hatvp.fr/agora/stock.json", True)

for act in hatvp[2]:
    if "num_organisation" not in act:
        continue
    if act["num_organisation"] not in actions:
        actions[act["num_organisation"]] = []
    reformat_date(act, "publicationDate")
    actions[act["num_organisation"]].append(act)

for org in hatvp[0] + hatvp[1]:
    if org["identifiantNational"] in done:
        continue
    done[org["identifiantNational"]] = True
    org["url_json"] = "https://www.hatvp.fr/agora/%s.json" % org["identifiantNational"]
    reformat_date(org, "datePremierePublication")
    details = safe_dl(org["url_json"])
    if details:
        reformat_date(details["publicationCourante"], "dateCreation")
        [reformat_date(h, "dateCreation") for h in details["historique"]]
        org.update(details["publicationCourante"])
        historique = [h for h in details["historique"] if h["dateCreation"] != org["dateCreation"]]
        org["historique"] = sorted(historique, key=lambda x: x["dateCreation"])
        org["actions"] = sorted(actions.get(org["identifiantNational"], None), key=lambda x: x["publicationDate"])
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
