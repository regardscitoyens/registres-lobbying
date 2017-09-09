#!/bin/bash

rooturl="http://www2.assemblee-nationale.fr/representant/representant_interet_"
url="${rooturl}liste"

mkdir -p rss
now=$(date -R)
echo "<?xml version=\"1.0\"?>
<rss version=\"2.0\">
 <channel>
  <title>RSS Registre des représentants d'intérêts Assemblée nationale</title>
  <link>$url</link>
  <description>Les dernières modifications au registre des représentants d'intérêts de l'Assemblée nationale</description>
  <pubDate>$now</pubDate>
  <generator>RegardsCitoyens https://github.com/regardscitoyens/registre-lobbying-AN</generator>" > rss/registre-lobbying-AN.rss
cat data/registre-lobbying-AN-v2.csv    |
  sed 's/^\([1-9]\),/0\1,/'             |
  sort -r                               |
  grep -v '^"id","'                     |
  while read line; do
    id=$(echo $line |
      sed 's/^0*\([0-9]\+\),.*$/\1/')
    nom=$(echo $line |
      sed 's/^[0-9]\+,"\(\([^"]\+\(""\)\?\)\+\)",.*$/\1/' |
      sed 's/""/"/g' |
      sed 's/\&/\&nbsp;/g')
    safenom=$(echo $nom |
      sed 's/\&nbsp;/\\\&/g' |
      sed 's/"/""/g')
    orgtype=$(echo $line |
      sed 's/^[0-9]\+,"'"$safenom"'",[^,]*,"\([^"]\+\)",.*$/\1/')
    dat="2013-12-31"
    if [ "$id" -gt 44 ]; then
      dat="2014-01-03"
    elif [ "$id" -gt 42 ]; then
      dat="2014-01-02"
    fi
    echo "  <item>
   <title>$nom ($orgtype, nouveau)</title>
   <link>${rooturl}details/$id</link>
   <description><![CDATA[Nouvel inscrit au registre le $(date "+%d %b %Y" -d "$dat") : $nom ($orgtype)]]></description>
   <pubDate>$(date -R -d "$dat")</pubDate>
  </item>" >> rss/registre-lobbying-AN.rss
  done
echo " </channel>
</rss>" >> rss/registre-lobbying-AN.rss

