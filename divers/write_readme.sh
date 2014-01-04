#!/bin/bash

regexp='^[0-9]\+,[^,]*,[^,]*,'
total=$(($(cat data/registre-lobbying-AN-v2.csv | wc -l) - 1))
civil=$(grep "$regexp\"\(Association\|Organisation non\)" data/registre-lobbying-AN-v2.csv | wc -l)
cabinets=$(grep "$regexp\"\(Cabinets\|Consultants\)" data/registre-lobbying-AN-v2.csv | wc -l)
prive=$(grep "$regexp\"Entreprise" data/registre-lobbying-AN-v2.csv | wc -l)
orgas=$(grep "$regexp\"\(\w*\s*[oO]rganisation pro\|Syndicat\)" data/registre-lobbying-AN-v2.csv | wc -l)
public=$(grep "$regexp\"\(Autorité\|Organisme\|Secteur\)" data/registre-lobbying-AN-v2.csv | wc -l)

echo "## Registre des représentants d'intérêts de l'Assemblée nationale

Le [nouveau registre des représentants d'intérêts de l'Assemblée nationale](http://www2.assemblee-nationale.fr/representant/representant_interet_liste) fournit un ensemble d'informations communiquées par souci de transparence par les organisations enregistrées.

Dans un souci d'archive, nous reproduisons sous la forme d'un tableur CSV [les données de l'ancienne version du registre](https://raw.github.com/regardscitoyens/registre-lobbying-AN/master/data/registre-lobbying-AN-v1-131229.csv) riche de 236 inscrits avant sa suppression le 29 décembre 2013. 

Pour aider l'Assemblée à mieux assurer ce souci de transparence, nous republions également les informations publiées sur le nouveau registre sous la forme de données réutilisables [CSV](https://raw.github.com/regardscitoyens/registre-lobbying-AN/master/data/registre-lobbying-AN-v2.csv) ou [JSON](https://raw.github.com/regardscitoyens/registre-lobbying-AN/master/data/registre-lobbying-AN-v2.json) sous conditions OpenData ([licence ODBL](http://www.vvlibri.org/fr/licence/odbl/10/fr/legalcode)).

Un total de $total organisations sont inscrites au registre depuis la dernière mise-à-jour le $(date "+%d %B %Y"), dont :
 + $cabinets agences de lobbying,
 + $prive entreprises,
 + $orgas syndicats ou organisations professionnelles,
 + $public organismes publics,
 + $civil organisations de la société civile.

Les données sont collectées et mises-à-jour en cas de modification toutes les 30 minutes.
Un [flux RSS](https://raw.github.com/regardscitoyens/registre-lobbying-AN/master/rss/registre-lobbying-AN.rss) permet ainsi d'être informé des futures modifications ou ajouts au registre.

[Regards Citoyens](http://www.regardscitoyens.org)

[Retrouvez nos études et plaidoyers sur l'encadrement du lobbying](http://www.regardscitoyens.org/etude-sur-le-lobbying-au-parlement/)" > README.md
