#!/bin/bash

DEBUG=true
if [ -z "$1" ]; then
  DEBUG=false
fi

rooturl="http://www2.assemblee-nationale.fr/representant/"
url="${rooturl}liste_representant_interet"
./divers_deprecie/scrap.py "$url" $1

if git diff data/registre-lobbying-AN-v2.csv |
  grep "." > /dev/null; then
  now=$(date -R)
  dat=$(date "+%d %b %Y")
  id=""
  action=""
  if test -f rss/registre-lobbying-AN.rss; then
    nl=$(cat rss/registre-lobbying-AN.rss | wc -l)
    tail -n $(($nl - 8)) rss/registre-lobbying-AN.rss |
      head -n $(($nl - 10)) > /tmp/registremore.tmp
  fi
  echo "<?xml version=\"1.0\"?>
<rss version=\"2.0\">
 <channel>
  <title>RSS Registre des représentants d'intérêts Assemblée nationale</title>
  <link>$url</link>
  <description>Les dernières modifications au registre des représentants d'intérêts de l'Assemblée nationale</description>
  <pubDate>$now</pubDate>
  <generator>RegardsCitoyens https://github.com/regardscitoyens/registre-lobbying-AN</generator>" > rss/registre-lobbying-AN.rss

  git diff data/registre-lobbying-AN-v2.csv     | 
    grep -v "/data/registre-lobbying-AN-v2.csv" |
    grep "^[-+]"                                |
    sed "s/^\([-+]\)\(.*\)$/\2;\1/"             |
    sort                                        |
    while read line; do
      oldid=$id
      oldaction=$action
      action=$(echo $line       |
        sed 's/^.*\([+-]\)$/\1/')
      id=$(echo $line           |
        sed 's/^\([0-9]\+\),.*$/\1/')
      nom=$(echo $line          |
        sed 's/^[0-9]\+,"\+\(\([^"]\+\(""\)\?\)\+\)"\+,.*$/\1/' |
        sed 's/""/"/g'          |
        sed 's/"\+$//'          |
        sed 's/\&/\&nbsp;/g')
      safenom=$(echo $nom       |
        sed 's/\&nbsp;/\\\&/g'  |
        sed 's|/|\\/|g'         |
        sed 's/"/""/g')
      orgtype=$(echo $line      |
        sed 's/^[0-9]\+,"\+'"$safenom"'"\+,[^,]*,"\([^"]\+\)",.*$/\1/')
      case "$action" in
        "+")
            desc="Nouvel inscrit a"
            statut="nouveau";;
        "-")
            desc="Retrait d"
            statut="retiré";;
      esac
      if [ "$id" != "$oldid" ] && [ -f "/tmp/registreitem.tmp" ] ; then
        cat /tmp/registreitem.tmp >> rss/registre-lobbying-AN.rss
      elif [ "$id" == "$oldid" ] && [ "$oldaction" != "$action" ]; then
        desc="Modifications des informations d"
        statut="modifié"
      fi
      echo "  <item>
   <title>$nom ($orgtype, $statut)</title>
   <link>${rooturl}detail_representant_interet/$id</link>
   <description><![CDATA[${desc}u registre le $dat : $nom ($orgtype)]]></description>
   <pubDate>$now</pubDate>
  </item>" > /tmp/registreitem.tmp
    done
  cat /tmp/registreitem.tmp >> rss/registre-lobbying-AN.rss
  rm -f /tmp/registreitem.tmp
  if test -s /tmp/registremore.tmp; then
    cat /tmp/registremore.tmp >> rss/registre-lobbying-AN.rss
  fi
  rm -f /tmp/registremore.tmp
  echo " </channel>
</rss>" >> rss/registre-lobbying-AN.rss
  ./divers_deprecie/write_readme.sh
  if ! $DEBUG; then
    git commit rss/registre-lobbying-AN.rss data/registre-lobbying-AN-v2.* README.md -m "update registre AN"
    git push
  fi
fi

