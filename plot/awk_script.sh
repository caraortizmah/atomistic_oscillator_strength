#!/bin/bash

# script to create .csv format to be used in python
# pre can be "socabsq" or "absq"
pre="$1"

suf=".out.${pre}.dat"
for vars in `ls *.out.${pre}.dat`
do
	job=${vars/%$suf}
	awk '{ printf "%s,%s,%s,%s,%s\n", $1, $2, $3, $4, $5  }' $vars > $job.csv
done
