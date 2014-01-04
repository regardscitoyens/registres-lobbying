#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import sep
import re, json

re_n = re.compile(r'^[\d\s]+$')

re_getnum = re.compile(r'^.*/(\d+)$')
get_num = lambda t: int(re_getnum.sub(r'\1', t))

def safeint(i):
    try: return int(i)
    except: return 0

split_val = lambda val: val.split(u" - ")

re_href = re.compile(r'^.*href="([^"]+)".*$', re.I)
re_cleanname = re.compile(r'\W')
re_cleanmontant = re.compile(r'^\s*(\d+)')
re_cleanwords = re.compile(r'^([\s\.]+|n[e%s]ant|non|aucune?|personne|ras|sans objet)$' % u'é', re.I)
cleancateg = lambda t: t.replace(u"Autres", u"Secteur public (autre)").replace(u"Autre organisme analogue", u"Autre organisation professionnelle")

# Nettoyage et découpage du html brut
pregexps = [
    (re.compile(r'\s*&nbsp;\s*'), u' '),
    (re.compile(r'[ \s\r\n]+'), u' '),
    (re.compile(r'(</?(dt|span|ul|tr))'), r'\n\1'),
]
def clean_html(h):
    for r, s in pregexps:
        h = r.sub(s, h)
    return h

# Nettoyage des données brutes
cregexps = [
    (re.compile(r'\s*<[\s/]*br[\s/]*>\s*'), u' '),
    (re.compile(r'<[^>]+>'), u''),
    (re.compile(r'\s*:\s*$'), u''),
    (re.compile(r'^\s*:\s*'), u''),
    (re.compile(r'\s\s+'), u''),
    (re.compile(r'^\s*'), u''),
    (re.compile(r'\s*$'), u''),
    (re.compile(r'^([\d\s]+)%s\s*(((sup|inf)%srieur\s*%s|Entre)\s*\d+.*%s)?$' % (u'€', u'é', u'à', u'€')), r'\1'),
    (re.compile(r'^([\s\.]+|n[e%s]ant|non|aucune?|personne|ras)$' % u'é', re.I), u'-'),
    (re.compile(r'^Association (loi (de )?|1901)+$', re.I), u'Association loi 1901'),
    (re.compile(r'^syndicat professionnel$', re.I), u"Syndycat professionnel"),
    (re.compile(r'^S\.*A\.*R\.*L\.*$', re.I), u'SARL'),
    (re.compile(r'^S(oci[e%s]t[e%s])?[.\s]*A(nonyme)?[.\s]*$', re.I), u'Société Anonyme'),
]
def clean_text(t):
    for r, s in cregexps:
        t = r.sub(s, t)
    if re_n.match(t):
        t = t.replace(' ', '')
        return int(t)
    t = t.lstrip('-, ')
    t = re_cleanwords.sub(u'-', t)
    return t

def save_json(filename, data):
    with open(sep.join(['data', '%s.json' % filename]), 'w') as f:
        json.dump(data, f, indent=True)

def save_csv(filename, data, keys):
    # Applatissement des données en liste et dict (un seul sous-niveau)
    flat = []
    for res in data:
        for k in res.keys():
            if isinstance(res[k], dict):
                d = res.pop(k)
                for k2, v in d.items():
                    k3 = "%s - %s" % (k, k2)
                    if k3 not in keys:
                        keys.append(k3)
                    if isinstance(v, list):
                        res[k3] = " - ".join([unicode(va) for va in v])
                    else:
                        res[k3] = v
            elif k not in keys:
                keys.append(k)
            if k in res and isinstance(res[k], list):
                res[k] = " - ".join([unicode(va) for va in res[k]])
        flat.append(res)
    dictk = {}
    for k in keys:
        dictk[k] = k
    flat.insert(0, dictk)

    with open(sep.join(['data', '%s.csv' % filename]), 'w') as f:
        for res in flat:
            f.write(",".join(["" if k not in res else unicode(res[k]).encode('utf-8') if re_n.match(unicode(res[k])) else "\"%s\"" % res[k].encode('utf-8').replace('"', '""') for k in keys]) + "\n")

