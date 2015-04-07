#!/bin/bash

cd $(echo $0 | sed 's#/[^/]*$##')

git pull > /dev/null 2>&1

rooturl="http://www2.assemblee-nationale.fr/representant/representant_interet_"
url="${rooturl}liste"
./scrap.py "$url" $1

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
   <link>${rooturl}detail/$id</link>
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
  ./divers/write_readme.sh
  git commit rss/registre-lobbying-AN.rss data/registre-lobbying-AN-v2.* README.md -m "update registre AN"
  git push
  
fi


# Check Sénat
urlsenat=$(curl http://www.senat.fr/role/groupes_interet.html 2> /dev/null |
  iconv -f iso-8859-15 -t utf-8 |
  grep "Liste des groupes d'" |
  sed 's|^.* href="\([^"]*\)".*$|http://www.senat.fr\1|')
filename=$(echo $urlsenat | sed 's|^.*/\([^/]\+\)$|data/\1|')
if ! test -f "$filename"; then
  echo 
  echo "---------------------------------------"
  echo "DOWNLOADING NEW SENATE REGISTER VERSION"
  echo "---------------------------------------"
  wget "$urlsenat" -O "$filename"
  source /usr/local/bin/virtualenvwrapper.sh
  workon registrelobbying
  in2csv "$filename" > "$filename.csv"
  ./clean_senat.py "$filename.csv" > data/registre-lobbying-Senat.csv
  rm -f "$filename.csv"
  git commit data/registre-lobbying-Senat.csv -m "update registre Sénat" 
  git push
fi

