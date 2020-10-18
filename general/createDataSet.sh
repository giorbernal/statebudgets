#!/bin/bash

DIR=datasets
BASE="$DIR/Presupuestos.txt"
FILE="$DIR/presupuestos.csv"
FILE_MELT="$DIR/presupuestos_melt.csv"

rm -fR $FILE
echo "parsing $FILE ..."
python ./createDataSet.py 1 $BASE > $FILE
echo "$FILE parsed!"

rm -fR $FILE_MELT
echo "melding $FILE_MELT ..."
python ./createDataSet.py 2 $FILE $FILE_MELT
echo "$FILE_MELT melt!"
