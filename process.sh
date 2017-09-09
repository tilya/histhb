#!/bin/bash

set -x

mv ~/downloads/1071024180207_*.pdf ~/misc/bankovni_vypisy/kb/
mv ~/downloads/189010981_*_MCZS.pdf ~/misc/bankovni_vypisy/era/

mv ~/downloads/1071024180207_*.csv ./src/
mv ~/downloads/189010981_*_MCZS.txt ./src/

enca -L cs -x utf8 src/*

ls ./src/1071024180207*.csv | xargs -n 1 -i ./histhb.py --bank kb --input "{}" --output out/kb_$(date +%s).csv

ls ./src/189010981_*_MCZS.txt | xargs -n 1 -i ./histhb.py --bank era --input "{}" --output out/era_$(date +%s).csv
