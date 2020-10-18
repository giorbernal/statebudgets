#!/bin/bash

DIR="datasets"
AGE="$DIR/edad2.csv"
AGE_MELT="$DIR/edad_melt.csv"
IMP="$DIR/tramos2.csv"
IMP_MELT="$DIR/tramos_melt.csv"

rm -fR $AGE_MELT
rm -fR $IMP_MELT

python createDataSet.py $AGE $AGE_MELT $IMP $IMP_MELT
