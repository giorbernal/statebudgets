#!/bin/bash

if [[ $# != 1 ]]; then
	echo 'Error in params: > ./createDataSet.sh <year>'
	exit -1
fi

YEAR=$1

DIR=datasets
BASE="$DIR/Presupuestos_$YEAR.txt"
FILE="$DIR/Presupuestos_$YEAR.csv"
FILE_MELT="$DIR/Presupuestos_${YEAR}_melt.csv"

rm -fR $FILE
echo "parsing $FILE ..."
python ./createDataSet.py --command PARSE --fileIn $BASE --year $YEAR > $FILE
echo "$FILE parsed!"

rm -fR $FILE_MELT
echo "melding $FILE_MELT ..."
python ./createDataSet.py --command MELT --fileIn $FILE --fileOut $FILE_MELT --year $YEAR
echo "$FILE_MELT melt!"
