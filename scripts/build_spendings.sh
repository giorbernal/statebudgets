#!/bin/sh
# Genera spendings.csv para presupuestos del estado español
# Skill: build-budgets-csv
# Soporta múltiples formatos de HTML (nuevo con <span>, antiguo con <div>)

if [[ $# != 1 ]]; then
  echo "error: invalid params!"
  echo "usage: scripts/build_spendings.sh <year>"
  exit -1
fi

YEAR=$1

WORKSPACE=$(pwd)
HTM_DIR="$WORKSPACE/pge/$YEAR/PGE-ROM/doc/HTM"
POLITICAS_FILE="$WORKSPACE/scripts/politicas_gasto.txt"
OUTPUT_CSV="$WORKSPACE/pge/$YEAR/spendings.csv"
TMP_ALL="$WORKSPACE/scripts/spendings_all.tmp"

rm -f "$OUTPUT_CSV" "$TMP_ALL"
echo "Generando $OUTPUT_CSV para año $YEAR..."

# Determinar el patrón de archivo según el año
# Años 2022+: N_22P_E_R_31_*_1_1_3_1.HTM (formato nuevo)
# Años 2019-2021: N_18P_E_R_31_*_1_1_3_1.HTM (formato antiguo)
YEAR_PREFIX=${YEAR:2:2}
PREV_YEAR=$((10#$YEAR_PREFIX - 1))

FILE_PATTERN_SUFFIX=E_R_31_*_1_1_3_1.HTM

FILE_PATTERN="N_${YEAR_PREFIX}_$FILE_PATTERN_SUFFIX"

# Verificar si existen archivos con el patrón del año actual
if ! ls "$HTM_DIR"/$FILE_PATTERN 1> /dev/null 2>&1; then
    FILE_PATTERN="N_${PREV_YEAR}_$FILE_PATTERN_SUFFIX"
    echo "Usando patrón de año anterior: $FILE_PATTERN"
    if ! ls "$HTM_DIR"/$FILE_PATTERN 1> /dev/null 2>&1; then
      FILE_PATTERN="N_${PREV_YEAR_PREFIX}P_$FILE_PATTERN_SUFFIX"
      echo "Usando patrón de prorroga: $FILE_PATTERN"
      if ! ls "$HTM_DIR"/$FILE_PATTERN 1> /dev/null 2>&1; then
        FILE_PATTERN="N_${PREV_YEAR}P_$FILE_PATTERN_SUFFIX"
        echo "Usando patrón de prorroga del año anterior: $FILE_PATTERN"
      else
        echo "Error. Ningún patron encontrado"
        exit -1
      fi
    fi
fi


echo "Patrón: $FILE_PATTERN"

# ── Función de decodificación de entidades HTML ─────────────────────────────────────
decode_entities() {
    awk '
    function decode(s,    result, code) {
        result = ""
        while (length(s) > 0) {
            if (match(s, /&#[0-9]+;/)) {
                result = result substr(s, 1, RSTART-1)
                code = substr(s, RSTART+2, RLENGTH-3) + 0
                if (code <= 127) {
                    result = result sprintf("%c", code)
                } else {
                    # Mapeo manual de caracteres UTF-8 comunes
                    if (code == 193) result = result "\xC3\x81"
                    else if (code == 201) result = result "\xC3\x89"
                    else if (code == 205) result = result "\xC3\x8D"
                    else if (code == 211) result = result "\xC3\x93"
                    else if (code == 218) result = result "\xC3\x9A"
                    else if (code == 225) result = result "\xC3\xA1"
                    else if (code == 233) result = result "\xC3\xA9"
                    else if (code == 237) result = result "\xC3\xAD"
                    else if (code == 243) result = result "\xC3\xB3"
                    else if (code == 250) result = result "\xC3\xBA"
                    else if (code == 241) result = result "\xC3\xB1"
                    else if (code == 209) result = result "\xC3\x91"
                    else if (code == 252) result = result "\xC3\xBC"
                    else if (code == 231) result = result "\xC3\xA7"
                    else if (code == 191) result = result "\xC2\xBF"
                    else if (code == 161) result = result "\xC2\xA1"
                    else if (code == 186) result = result "\xC2\xBA"
                    else if (code == 170) result = result "\xC2\xAA"
                    else result = result "?"
                }
                s = substr(s, RSTART+RLENGTH)
            } else {
                result = result s
                s = ""
            }
        }
        return result
    }
    { print decode($0) }
    '
}

# ── Determinar tipo de estructura HTML (span vs div) ─────────────────────────────
detect_html_type() {
    local htm="$1"
    local span_count=$(iconv -f windows-1252 -t utf-8 "$htm" 2>/dev/null | grep -c "<span" || echo 0)
    
    if [ "$span_count" -gt 0 ]; then
        echo "span"
    else
        echo "div"
    fi
}

# ── Procesar cada ficheo HTM ─────────────────────────────────────────────────────
for htm in $(ls "$HTM_DIR"/$FILE_PATTERN 2>/dev/null | sort); do
    fname=$(basename "$htm")
    
    # Detectar tipo de HTML
    html_type=$(detect_html_type "$htm")
    
    if [ "$html_type" = "span" ]; then
        # Formato nuevo (2022+): usar <span> tags
        iconv -f windows-1252 -t utf-8 "$htm" 2>/dev/null \
          | sed 's/<span[^>]*>/\n__SPAN__/g; s/<\/span>/__ENDSPAN__\n/g' \
          | grep "__SPAN__" \
          | sed 's/^__SPAN__//; s/__ENDSPAN__$//' \
          | decode_entities \
          | awk '
            BEGIN { found_header = 0; ncols = 0; buf_count = 0; seccion = ""; counting_header = 0; header_count = 0 }

            !found_header && /Secci/ && !/Clasif/ {
                if (match($0, /: /)) {
                    seccion = substr($0, RSTART + 2)
                    gsub(/^[[:space:]]+|[[:space:]]+$/, "", seccion)
                }
            }

            !found_header && /^Clasif\./ {
                counting_header = 1
                header_count = 1
                next
            }

            counting_header && !found_header {
                header_count++
                if ($0 == "Total") {
                    ncols = header_count
                    found_header = 1
                    counting_header = 0
                    buf_count = 0
                }
                next
            }

            found_header && ncols > 0 {
                buf[buf_count] = $0
                buf_count++

                if (buf_count == ncols) {
                    clasif = buf[0]
                    expl   = buf[1]
                    total  = buf[ncols - 1]
                    buf_count = 0

                    if (clasif !~ /^[0-9][0-9][0-9][A-Za-z0-9]$/) next
                    if (expl ~ /^TOTAL/) next
                    if (total == "") next

                    if (clasif ~ /^000/) {
                        expl = expl " (Sección: " seccion ")"
                    }

                    print clasif "|" expl "|" total
                }
            }
          ' >> "$TMP_ALL"
    else
        # Formato antiguo (2019-2021): buscar en <div> tags
        iconv -f windows-1252 -t utf-8 "$htm" 2>/dev/null \
          | sed 's/<div[^>]*>/\n__DIV__/g; s/<\/div>/__ENDDIV__\n/g' \
          | grep -v "^__DIV__<" \
          | grep "__DIV__" \
          | sed 's/^__DIV__//; s/__ENDDIV__$//' \
          | decode_entities \
          | awk '
            BEGIN { found_header = 0; ncols = 0; buf_count = 0; seccion = ""; counting_header = 0; header_count = 0 }

            !found_header && /Secci/ && !/Clasif/ {
                if (match($0, /: /)) {
                    seccion = substr($0, RSTART + 2)
                    gsub(/^[[:space:]]+|[[:space:]]+$/, "", seccion)
                }
            }

            !found_header && /^Clasif\./ {
                counting_header = 1
                header_count = 1
                next
            }

            counting_header && !found_header {
                header_count++
                if ($0 == "Total") {
                    ncols = header_count
                    found_header = 1
                    counting_header = 0
                    buf_count = 0
                }
                next
            }

            found_header && ncols > 0 {
                buf[buf_count] = $0
                buf_count++

                if (buf_count == ncols) {
                    clasif = buf[0]
                    expl   = buf[1]
                    total  = buf[ncols - 1]
                    buf_count = 0

                    if (clasif !~ /^[0-9][0-9][0-9][A-Za-z0-9]$/) next
                    if (expl ~ /^TOTAL/) next
                    if (total == "") next

                    if (clasif ~ /^000/) {
                        expl = expl " (Sección: " seccion ")"
                    }

                    print clasif "|" expl "|" total
                }
            }
          ' >> "$TMP_ALL"
    fi

    count=$(wc -l < "$TMP_ALL" 2>/dev/null)
    if [ -z "$count" ]; then count=0; fi
    count=$(echo "$count" | tr -d ' ')
    echo "  $fname procesado (acumulado: $count filas)"
done

total_raw=$(wc -l < "$TMP_ALL" 2>/dev/null)
if [ -z "$total_raw" ]; then total_raw=0; fi
total_raw=$(echo "$total_raw" | tr -d ' ')
echo ""
echo "Líneas extraídas en bruto: $total_raw"

# ── Cruzar con políticas de gasto ────────────────────────────────────────────────
if [ -f "$POLITICAS_FILE" ]; then
    awk -v pfile="$POLITICAS_FILE" '
    BEGIN {
        while ((getline line < pfile) > 0) {
            prefix = substr(line, 1, 2)
            politica[prefix] = line
        }
    }
    {
        n = split($0, fields, "|")
        clasif = fields[1]
        expl   = fields[2]
        total  = fields[3]
        prefix = substr(clasif, 1, 2)
        pol = (prefix in politica) ? politica[prefix] : ""
        print clasif "|" expl "|" total "|" pol
    }
    ' "$TMP_ALL" > /tmp/spendings_with_pol.tmp
else
    cp "$TMP_ALL" /tmp/spendings_with_pol.tmp
    echo "ADVERTENCIA: No se encontró $POLITICAS_FILE"
fi

# ── Política más frecuente (para 000X) ────────────────────────────────────────────
politica_frecuente=$(awk -F'|' '
$1 !~ /^000/ && $4 != "" { count[$4]++ }
END {
    max = 0; best = ""
    for (p in count) { if (count[p] > max) { max = count[p]; best = p } }
    print best
}
' /tmp/spendings_with_pol.tmp)

echo "Política más frecuente (para 000X): $politica_frecuente"

# ── Escribir CSV final ────────────────────────────────────────────────────────────
awk -F'|' -v pfrecuente="$politica_frecuente" '
{
    clasif = $1; expl = $2; total = $3; pol = $4
    if (clasif ~ /^000/ && pol == "") pol = pfrecuente
    print clasif ";" expl ";" total ";" pol
}
' /tmp/spendings_with_pol.tmp > "$OUTPUT_CSV"

total_filas=$(wc -l < "$OUTPUT_CSV")
echo ""
echo "CSV generado: $OUTPUT_CSV"
echo "Total de filas: $total_filas"
echo ""
echo "Primeras 10 líneas:"
head -10 "$OUTPUT_CSV"

rm -f "$TMP_ALL" /tmp/spendings_with_pol.tmp
