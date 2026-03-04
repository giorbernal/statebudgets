#!/bin/sh
# Ensemble all spending.csv files into a single global file
# Skill: build-budgets-csv

WORKSPACE=$(pwd)
DATA_DIR="$WORKSPACE/data/input"
PGE_DIR="$WORKSPACE/pge"
OUTPUT_FILE="$DATA_DIR/spending.csv"

if [ ! -d "$PGE_DIR" ]; then
    echo "Error: pge directory not found. Please ensure budget data is present."
    exit 1
fi

mkdir -p "$DATA_DIR"

rm -f "$OUTPUT_FILE"
echo "year,code,name,amount,policy" >> "$OUTPUT_FILE"
echo "Ensembling spending.csv files..."

for year_dir in $(ls -d "$PGE_DIR"/[0-9]* 2>/dev/null | sort -t/ -k6 -n); do
    year=$(basename "$year_dir")
    csv_file="$year_dir/spending.csv"
    
    if [ -f "$csv_file" ]; then
        echo "  Adding $year ($csv_file)"
        
        awk -F';' -v year="$year" '
        BEGIN { OFS = ";" }
        {
            print year, $0
        }
        ' "$csv_file" >> "$OUTPUT_FILE"
    else
        echo "  Skip $year (spending.csv not found)"
    fi
done

total=$(wc -l < "$OUTPUT_FILE" 2>/dev/null || echo 0)
echo ""
echo "Generated: $OUTPUT_FILE"
echo "Total rows: $total"
echo ""
echo "First 5 lines:"
head -5 "$OUTPUT_FILE"
