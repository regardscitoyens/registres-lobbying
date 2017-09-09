#!/bin/bash

cd $(echo $0 | sed 's#/[^/]*$##')

git pull > /dev/null 2>&1

DEBUG=true
if [ -z "$1" ]; then
  DEBUG=false
fi

# Update AN (obsolète)
# ./divers_deprecie/update_an.sh

# Check Sénat
urlsenat=$(curl http://www.senat.fr/role/groupes_interet.html 2> /dev/null |
  iconv -f iso-8859-15 -t utf-8 |
  grep "Liste des représentants d'" |
  head -n 1 |
  sed 's|^.* href="\([^"]*xlsx\?\)".*$|http://www.senat.fr\1|')
filename=$(echo $urlsenat | sed 's|^.*/\([^/]\+\)$|data/\1|')
if ! [ -z "$filename" ] && ! test -f "$filename"; then
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
  if ! $DEBUG; then
    git commit data/registre-lobbying-Senat.csv -m "update registre Sénat"
    git push
  fi
fi

