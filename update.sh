#!/bin/bash

cd $(echo $0 | sed 's#/[^/]*$##')

git stash && git pull && git stash pop > /dev/null 2>&1

#source /usr/local/bin/virtualenvwrapper.sh
#workon registrelobbying
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"    # if `pyenv` is not already on PATH
eval "$(pyenv init --path)"                                                                                                                                                                                                              
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
export PYENV_VIRTUALENV_DISABLE_PROMPT=1
pyenv activate registrelobbying

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
  sed 's#^.* href="\([^"]*\.\(xlsx\?\|pdf\)\)".*$#http://www.senat.fr\1#')
filename=$(echo $urlsenat | sed 's|^.*/\([^/]\+\)$|data/\1|')
if ! [ -z "$filename" ] && ! test -f "$filename"; then
  echo 
  echo "---------------------------------------"
  echo "DOWNLOADING NEW SENATE REGISTER VERSION"
  echo "---------------------------------------"
  wget "$urlsenat" -O "$filename"
  if echo $urlsenat | grep xls > /dev/null; then
    in2csv -H "$filename" > "$filename.csv"
    ./clean_senat.py "$filename.csv" > data/registre-lobbying-Senat.csv
    rm -f "$filename.csv"
    if ! $DEBUG; then
      git commit data/registre-lobbying-Senat.csv -m "update registre Sénat"
      git push
    fi
  else
    cp -f "$filename" "data/registre-lobbying-Senat.pdf"
    if ! $DEBUG; then
      git add data/registre-lobbying-Senat.pdf
      git commit -m "update registre Sénat"
      git push
    fi
  fi
fi

# Check HATVP
./scrap_hatvp.py
if ! $DEBUG && git diff data/registre-lobbying-HATVP*.json images | grep "." > /dev/null; then
  git add images data/registre-lobbying-HATVP*.json
  git commit -m "update registre HATVP"
  git push
fi
