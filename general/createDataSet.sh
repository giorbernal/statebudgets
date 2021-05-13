#!/bin/bash

if [[ $# != 0 ]]; then
	echo 'Error in params: > ./createDataSet.sh'
	exit -1
fi

DIR=datasets
BASE="$DIR/Presupuestos_2021.txt"
FILE="$DIR/Presupuestos_2021.csv"

rm -fR $FILE
echo "parsing $FILE ..."
python ./createDataSet.py --fileIn $BASE --fileOut $FILE
echo "$FILE parsed!"
