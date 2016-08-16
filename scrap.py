#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from sys import argv, stderr, exit
from time import sleep
from os import mkdir
from os.path import sep, exists as fileexists
from urllib2 import urlopen, HTTPError, URLError
from httplib import BadStatusLine
from utils import *

# Deuxième argument optionnel active l'usage du cache pour le debug
cache = len(argv) > 2

# Prend comme argument l'url de la liste des représentants et reconstruit les urls relatives en fonction du domaine
url = argv[1]
rooturl = re.sub(r'^(https?://[^/]+).*$', r'\1', url, re.I)
geturl = lambda t: re_href.sub(r'%s\1' % rooturl, t)
filename = "registre-lobbying-AN-v2"

re_clean_title = re.compile(r'<title>.*</title>')
clean_nonutf_title = lambda x: re_clean_title.sub("", x)

def download(url, attempts_left=3):
    try:
        return urlopen(url).read()
    except (HTTPError, URLError, BadStatusLine) as e:
        if attempts_left:
            sleep(5)
            return download(url, attempts_left-1)
        stderr.write("ERROR downloading %s: %s" % (url, e))
        exit(1)

try:
    mkdir('cache')
except:
    pass
# Télécharge archive en cache et nettoie une page
def get_html(url, name):
    cachefile = sep.join(["cache", "%s.html" % name])
    if not cache:
        h = download(url)
        with open(cachefile, 'w') as f:
            f.write(h)
    else:
        with open(cachefile, 'r') as f:
            h = f.read()
    h = clean_nonutf_title(h)
    h = h.decode('utf-8')
    h = clean_html(h)
    return h

ANdoublons = {}
if fileexists('doublonsAN.json'):
    with open('doublonsAN.json') as f:
        ANdoublons = dict((int(k), v) for k, v in json.load(f).items())
    with open('data/registre-lobbying-AN-v2.json') as f:
        oldData = dict((dic[u'id'], dic) for dic in json.load(f))

# Extrait les informations de la fiche détaillée d'un représentant
def extract_data(text):
    res = {}
    sublevel = False
    field, spefield = "", ""
    val = res
    for line in text.split('\n'):
        if line.startswith('<dt'):
            spefield = clean_text(line)
        elif line.startswith('</ul'):
            val = res
        elif line.startswith('<ul'):
            if field:
                sublevel = True
            elif spefield and not spefield in res:
                res[spefield] = clean_text(line)
                if spefield == u"Site internet" and not res[spefield].startswith('http'):
                    res[spefield] = u"http://%s" % res[spefield]
        elif line.startswith('<span'):
            cont = clean_text(line)
            if 'class="nom-champ"' in line:
                if sublevel:
                    res[field] = {}
                    val = res[field]
                field = cont
                if field in val:
                    raise Exception("Field %s found twice" % field)
                val[field] = ""
            elif 'class="data"' in line and cont and cont != "-":
                if isinstance(val[field], list):
                    val[field].append(cont)
                elif val[field]:
                    val[field] = [val[field], cont]
                else:
                    val[field] = cont
            sublevel = False
    return res

re_split_line = re.compile(r'</td> <td[^>]*>', re.I)
# Télécharge la liste des représentnts et itère dessus
data = []
listpage = get_html(url, "liste")

for line in listpage.split('\n'):
    res = {}

    # Identifie lignes d'enregistrement
    if 'bullet_arrow_large.png' not in line:
        continue

    # Récupère premières infos standard
    match = re_split_line.split(line)
    res[u'Raison sociale'] = clean_text(match[0])
    res[u'Catégorie'] = clean_text(match[1])
    res[u'Catégorie'] = cleancateg(res[u'Catégorie'])
    res[u'URL registre Assemblée'] = geturl(match[3])
    res[u'id'] = get_num(res[u'URL registre Assemblée'])
    if res[u'id'] in ANdoublons:
        data.append(oldData[ANdoublons[res[u'id']]])
        continue
    name = re_cleanname.sub('_', res[u'Raison sociale'])

    # Télécharge et complète les infos tirées de la fiche détaillée du représentant
    text = get_html(res[u'URL registre Assemblée'], name)
    res.update(extract_data(text))

    # Transforme en liste certains champs
    if u"Domaines d'activité et centres d'intérêt" in res:
        split_val(res[u"Domaines d'activité et centres d'intérêt"])
    if u"Les adhérents" in res:
        split_val(res[u"Les adhérents"][u"Noms des personnes morales membres de l'organisme"])
        if not isinstance(res[u"Les adhérents"][u"Nature juridique des adhérents"], list):
            res[u"Les adhérents"][u"Nature juridique des adhérents"] = [a.strip() for a in res[u"Les adhérents"][u"Nature juridique des adhérents"].split(' - ') if not re_cleanwords.match(a.strip('. '))]

    # Nettoie les infos inutiles sur la gamme quand le montant est fourni
    for field in res:
        if u"Chiffre d'affaires" in field or u"activités directes de représentation" in field:
            res[field] = re_cleanmontant.sub(r'\1', unicode(res[field]))

    # Consolide les données similaires venues de différents formulaires
    # - Budget global à partir de CA global ou budget global
    if not u"Budget global" in res:
        try:
            res[u"Budget global"] = res[u"Chiffre d'affaire de l'entreprise ou du groupe"]
        except:
            res[u"Budget global"] = res[u"Chiffre d'affaire lié aux activités directes de représentation d'intérêts effectués pour le compte de client auprès du Parlement"]
    # - Nombre d'employés et salariés combinés
    if u"Nombre de personnes employées par l'organisme" not in res:
        field = u"Nombre de personnes participant aux activités qui relèvent du champ d'application du registre des représentants"
        if u"Nombre de salariés dans l'entreprise ou dans le groupe" in res:
            res[u"Nombre de personnes employées par l'organisme"] = safeint(res[u"Nombre de salariés dans l'entreprise ou dans le groupe"][u"En France"]) + safeint(res[u"Nombre de salariés dans l'entreprise ou dans le groupe"][u"A l'étranger"])
        elif field in res:
            if isinstance(res[field], list):
                res[u"Nombre de personnes employées par l'organisme"] = res[field][0]
            else:
                res[u"Nombre de personnes employées par l'organisme"] = res[field]
    # - Budget lié au lobbying = CA pour cabinets
    field = u"Budget lié aux activités directes de représentation d'intérêts auprès du Parlement"
    try:
        res[field] = res[u"Chiffre d'affaire lié aux activités directes de représentation d'intérêts effectués pour le compte de client auprès du Parlement"]
    except:
        res[field] = res[u"Coûts liés aux activités directes de représentation d'intérêts auprès du Parlement"]

    data.append(res)

# Sauve JSON
save_json(filename, data)

# Sauve CSV
# Liste des headers pour assurer l'ordre du csv
keys = [
    u'id',
    u'Raison sociale',
    u'Acronyme',
    u'Catégorie',
    u'URL registre Assemblée',
    u'Statut légal',
    u'Site internet',
    u'Objectif et mission',
    u"Domaines d'activité et centres d'intérêt",
    u'Dirigeant / personne juridiquement responsable',
    u'Personnes bénéficiaires de la carte de représentant',
    u'Adresse et téléphone',
    u"Nombre de personnes participant aux activités qui relèvent du champ d'application du registre des représentants",
    u"Principales initiatives liées à l'Assemblée nationale couvertes l'année précédente",
    u'Adhésion à un code de conduite, une charte éthique ou une charte sur le lobbying',
    u'Appartenance à un(e) ou plusieurs réseau(x) / association(s) / fédération(s) / confédération(s)',
    u'Année ou période du dernier exercice comptable',
    u'Budget global',
    u'Dont financement public',
    u'Autres sources - Dons',
    u'Autres sources - Cotisations des membres',
    u'Autres sources - Autres',
    u'Autres sources - Commercialisation de produits, services',
    u"Chiffre d'affaire de l'entreprise ou du groupe",
    u"Répartition du chiffre d'affaire pour chaque domaine d'activité",
    u"Chiffre d'affaire lié aux activités directes de représentation d'intérêts effectués pour le compte de client auprès du Parlement",
    u"Coûts liés aux activités directes de représentation d'intérêts auprès du Parlement",
    u"Budget lié aux activités directes de représentation d'intérêts auprès du Parlement",
    u'Information financière complémentaire',
    u'Nom des clients',
    u"Nombre de personnes employées par l'organisme",
    u"Nombre de salariés dans l'entreprise ou dans le groupe - En France",
    u"Nombre de salariés dans l'entreprise ou dans le groupe - A l'étranger",
    u'Les adhérents - Nature juridique des adhérents',
    u'Les adhérents - Nombre total d\'adhérents "personnes physiques"',
    u'Les adhérents - Nombre total d\'adhérents "personnes morales"',
    u"Les adhérents - Noms des personnes morales membres de l'organisme",
]
save_csv(filename, data, keys)
