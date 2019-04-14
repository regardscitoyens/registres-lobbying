#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, csv, re
from datetime import date

handtypos = [
  ("FP2E,Fédération professionnelle,MATHIEU,Tristan,", "FP2E,Fédération professionnelle,MATHIEU Tristan,,"),
  ("Afrique Inelligence", "Afrique Intelligence"),
  ("Gontard Jean Henri", "GONTARD Jean Henri"),
  ("A31:F31Secours catholique", "Secours catholique"),
  (",Assocation,", ",Association,"),
]
def clean_bad_data(data):
    for line in data:
        for typo, fix in handtypos:
            line = line.replace(typo, fix)
        yield line

with open(sys.argv[1]) as f:
    xls = list(csv.reader(clean_bad_data(f)))


headers = [
  "Organisme",
  "Nature de l'organisme",
  "Nom de famille",
  "Prénom",
  "Fonction",
  "Intérêts représentés",
  "Date d'échéance du titre d'accès"
]


fmt = lambda t: '"%s"' % t.replace('"', '""') if "," in t else t
fml = lambda l: ",".join([fmt(t) for t in l])
caps = '[A-ZÀÂÉÈÊËÎÏÔÖÙÛÜÇ\-\s]'
re_splitname = re.compile(r'^(.*%s{4,}) (%s[a-zàâéèêëîïôöùûüç\-\s]+.*)$' % (caps, caps))
re_splitname2 = re.compile(r'^(%s[a-zàâéèêëîïôöùûüç\-\s]+.*) (%s{4,}.*)$' % (caps, caps))

def apply_regexps(regexps, t):
    for reg, sub in regexps:
        t = reg.sub(sub, t)
    return t.strip()

clean_regexps = [
  (re.compile(r'\s*\n+\s*'), ' '),
  (re.compile(r'^\s*-\s*'), ''),
  (re.compile(r'\s*[,-]+\s*$'), ''),
  (re.compile(r',\s*-\s*'), ' - '),
  (re.compile(r'\s+'), ' ')
]
clean = lambda t: apply_regexps(clean_regexps, t)

clean_accents_regexps = [
  (re.compile(r'[éèêëÉÈÊË]'), 'e'),
  (re.compile(r'[àâäÀÂÄ]'), 'a'),
  (re.compile(r'[îïÎÏ]'), 'i'),
  (re.compile(r'[ôöÔÖ]'), 'o'),
  (re.compile(r'[ùûüÙÛÜ]'), 'u'),
  (re.compile(r'[çÇ]'), 'c'),
]
fmtorder = lambda l: apply_regexps(clean_accents_regexps, l.lower().replace(' ', ''))

read = False
results = []
for line in xls:
    if line[0] == "Organisme":
        read = True
        keys = dict([(clean(v), k) for k, v in enumerate(line)])
        get = lambda l, k: clean(l[keys[k]]) if k in keys else ""
        continue
    elif not read:
        continue
    rep = dict([(k, get(line, k)) for k in headers])
    rep["Nature de l'organisme"] = get(line, "Nature de l'Organisme")
    try:
        rep["Nom de famille"], rep["Prénom"] = re_splitname.search(get(line, "Nom et prénom du détenteur du titre")).groups()
    except:
        try:
            rep["Prénom"], rep["Nom de famille"] = re_splitname2.search(get(line, "Nom et prénom du détenteur du titre")).groups()
        except:
            rep["Nom de famille"] = get(line, "Nom et prénom du détenteur du titre")
            rep["Prénom"] = ""
            print >> sys.stderr, "WARNING: error extracting surname from family name:", rep["Nom de famille"]
    try:
        dat = date.fromtimestamp((float(get(line, "Date d'échéance du titre d'accès"))-25569)*86400)
        rep["Date d'échéance du titre d'accès"] = "%02d/%02d/%04d" % (dat.day, dat.month, dat.year)
    except:
        if not rep["Date d'échéance du titre d'accès"]:
            rep["Date d'échéance du titre d'accès"] = results[-1]["Date d'échéance du titre d'accès"]
        else:
            rep["Date d'échéance du titre d'accès"] = re.sub(r'(\d{4})-(\d{2})-(\d{2})', r'\3/\2/\1', rep["Date d'échéance du titre d'accès"])
    results.append(rep)

print fml(headers)
for rep in sorted(results, key=lambda r: fmtorder(r["Organisme"])):
    print fml([rep[k] for k in headers])
