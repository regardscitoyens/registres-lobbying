#!/bin/bash

cd $(echo $0 | sed 's#/[^/]*$##')

url="http://www2.assemblee-nationale.fr/representant/representant_interet_liste"
./scrap.py "$url" $1

