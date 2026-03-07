#!/bin/bash
# Genera spending.csv para presupuestos del estado español
# Skill: build-budgets-csv
# Soporta múltiples formatos de HTML (nuevo con <span>, antiguo con <div>)

if [[ $# != 1 ]]; then
  echo "error: invalid params!"
  echo "usage: scripts/build_spending.sh <year>"
  exit -1
fi

YEAR=$1

WORKSPACE=$(pwd)
HTM_DIR="$WORKSPACE/pge/$YEAR/PGE-ROM/doc/HTM"
POLITICAS_FILE="$WORKSPACE/scripts/politicas_gasto.txt"
OUTPUT_CSV="$WORKSPACE/pge/$YEAR/spending.csv"
TMP_ALL="$WORKSPACE/scripts/spending_all.tmp"

rm -f "$OUTPUT_CSV" "$TMP_ALL"
echo "Generando $OUTPUT_CSV para año $YEAR..."

# Determinar el patrón de archivo según el año
# Años 2022+: N_22P_E_R_31_*_1_1_3_1.HTM (formato nuevo)
# Años 2019-2021: N_18P_E_R_31_*_1_1_3_1.HTM (formato antiguo)
YEAR_PREFIX=${YEAR:2:2}
PREV_YEAR=$((10#$YEAR_PREFIX - 1))

# Determinando sufijo del patron de ficheros según año
if [ $YEAR -gt 2013 ]; then
  FILE_PATTERN_SUFFIX=E_R_31_*_1_1_3_1.HTM
else
  FILE_PATTERN_SUFFIX=E_R_31_*_1_1_7.HTM
fi

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
        if ! ls "$HTM_DIR"/$FILE_PATTERN 1> /dev/null 2>&1; then
          echo "Error. Ningún patron encontrado"
          exit -1
        fi
      fi
    fi
fi


echo "Patrón: $FILE_PATTERN"

# ── Función de decodificación de entidades HTML ─────────────────────────────────────
decode_entities() {
    awk '
    function decode(s,    result, code, entity) {
        result = ""
        while (length(s) > 0) {
            # Primero procesar entidades numéricas (&#233;)
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
            }
            # Luego procesar entidades nombradas (&eacute;, &aacute;, etc.)
            else if (match(s, /&[a-zA-Z]+;/)) {
                result = result substr(s, 1, RSTART-1)
                entity = substr(s, RSTART+1, RLENGTH-2)
                
                # Mapeo de entidades HTML comunes españolas
                if (entity == "aacute") result = result "\xC3\xA1"
                else if (entity == "eacute") result = result "\xC3\xA9"
                else if (entity == "iacute") result = result "\xC3\xAD"
                else if (entity == "oacute") result = result "\xC3\xB3"
                else if (entity == "uacute") result = result "\xC3\xBA"
                else if (entity == "Aacute") result = result "\xC3\x81"
                else if (entity == "Eacute") result = result "\xC3\x89"
                else if (entity == "Iacute") result = result "\xC3\x8D"
                else if (entity == "Oacute") result = result "\xC3\x93"
                else if (entity == "Uacute") result = result "\xC3\x9A"
                else if (entity == "aacute") result = result "\xC3\xA1"
                else if (entity == "acirc") result = result "\xC3\xA2"
                else if (entity == "Acirc") result = result "\xC3\x82"
                else if (entity == "ocirc") result = result "\xC3\xB4"
                else if (entity == "Ocirc") result = result "\xC3\x94"
                else if (entity == "ecirc") result = result "\xC3\xAA"
                else if (entity == "Ecirc") result = result "\xC3\x8A"
                else if (entity == "icirc") result = result "\xC3\xAE"
                else if (entity == "Icirc") result = result "\xC3\x8E"
                else if (entity == "ucirc") result = result "\xC3\xBB"
                else if (entity == "Ucirc") result = result "\xC3\x9B"
                else if (entity == "ntilde") result = result "\xC3\xB1"
                else if (entity == "Ntilde") result = result "\xC3\x91"
                else if (entity == "uuml") result = result "\xC3\xBC"
                else if (entity == "Uuml") result = result "\xC3\x9C"
                else if (entity == "ccedil") result = result "\xC3\xA7"
                else if (entity == "Ccedil") result = result "\xC3\x87"
                else if (entity == "iquest") result = result "\xC2\xBF"
                else if (entity == "iexcl") result = result "\xC2\xA1"
                else if (entity == "ordf") result = result "\xC2\xBA"
                else if (entity == "ordm") result = result "\xC2\xBA"
                else if (entity == "ordf") result = result "\xC2\xAA"
                else if (entity == "agrave") result = result "\xC3\xA0"
                else if (entity == "egrave") result = result "\xC3\xA8"
                else if (entity == "igrave") result = result "\xC3\xAC"
                else if (entity == "ograve") result = result "\xC3\xB2"
                else if (entity == "ugrave") result = result "\xC3\xB9"
                else if (entity == "quot") result = result "\""
                else if (entity == "amp") result = result "&"
                else if (entity == "lt") result = result "<"
                else if (entity == "gt") result = result ">"
                else result = result "&" entity ";"
                
                s = substr(s, RSTART+RLENGTH)
            } else {
                result = result substr(s, 1, 1)
                s = substr(s, 2)
            }
        }
        return result
    }
    { print decode($0) }
    '
}

# ── Determinar tipo de estructura HTML (span vs div vs table) ──────────────────────
detect_html_type() {
    local htm="$1"
    local span_count div_count table_count
    
    span_count=$(iconv -f windows-1252 -t utf-8 "$htm" 2>/dev/null | grep -c "<span")
    if [ $? -ne 0 ] || [ -z "$span_count" ]; then span_count=0; fi
    
    div_count=$(iconv -f windows-1252 -t utf-8 "$htm" 2>/dev/null | grep -c "<div")
    if [ $? -ne 0 ] || [ -z "$div_count" ]; then div_count=0; fi
    
    table_count=$(iconv -f windows-1252 -t utf-8 "$htm" 2>/dev/null | grep -c "<table")
    if [ $? -ne 0 ] || [ -z "$table_count" ]; then table_count=0; fi
    
    # 2022+ format uses <span> tags (1+ spans)
    if [ "$span_count" -gt 0 ]; then
        echo "span"
    # 2014-2021 format uses lowercase <div> tags (divs >= tables)
    elif [ "$div_count" -ge "$table_count" ]; then
        echo "div"
    # 2013 format uses <DIV> tags (uppercase) - need table parsing
    else
        echo "table"
    fi
}

# ── Procesar cada ficheo HTM ─────────────────────────────────────────────────────
for htm in $(ls "$HTM_DIR"/$FILE_PATTERN 2>/dev/null | sort); do
    fname=$(basename "$htm")
    
    # Detectar tipo de HTML
    html_type=$(detect_html_type "$htm")
    
    # Para años 2011-2013, forzar formato table
    if [ "$YEAR" -le 2013 ]; then
        html_type="table"
    fi
    
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
    elif [ "$html_type" = "div" ]; then
        # Formato antiguo (2014-2021): buscar en <div> tags
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
    elif [ "$html_type" = "table" ]; then
        # Formato 2011-2013: usar <DIV> tags (case-insensitive)
        # Las tablas tienen estructura variable, necesitamos detectar la última columna numérica
        iconv -f windows-1252 -t utf-8 "$htm" 2>/dev/null \
          | sed 's/<DIV[^>]*>/\n__DIV__/gi; s/<\/DIV>/__ENDDIV__\n/gi' \
          | sed 's/<TD[^>]*>/__TD__/gi; s/<\/TD>/\n/gi' \
          | grep -v "^__DIV__<" \
          | grep "__DIV__\|__TD__" \
          | sed 's/^__DIV__//; s/__ENDDIV__$//' \
          | decode_entities \
          | awk '
            BEGIN { 
                found_header = 0; ncols = 0; buf_count = 0; seccion = ""; counting_header = 0; header_count = 0
                last_numeric_col = -1
            }

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
                # Buscar la última columna que tenga "Total" en el header
                if ($0 ~ /Total/) {
                    ncols = header_count
                    found_header = 1
                    counting_header = 0
                    buf_count = 0
                }
                # También contar si es la última columna del header
                if (header_count > 8) {
                    ncols = header_count
                    found_header = 1
                    counting_header = 0
                    buf_count = 0
                }
                next
            }

            # Saltar líneas que son solo marcadores de celda vacía
            /^__TD__$/ { next }

            found_header && ncols > 0 {
                buf[buf_count] = $0
                buf_count++

                if (buf_count == ncols) {
                    clasif = buf[0]
                    expl   = buf[1]
                    
                    # Buscar la última columna que tenga un valor numérico válido
                    total = ""
                    for (i = ncols - 1; i >= 0; i--) {
                        if (buf[i] ~ /^[0-9]+(\.[0-9]{3})*,[0-9]{2}$/) {
                            total = buf[i]
                            break
                        }
                    }
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
    ' "$TMP_ALL" > /tmp/spending_with_pol.tmp
else
    cp "$TMP_ALL" /tmp/spending_with_pol.tmp
    echo "ADVERTENCIA: No se encontró $POLITICAS_FILE"
fi

# ── Escribir CSV final (para 000X usar política del registro anterior) ──────────────
awk -F'|' '
{
    clasif = $1; expl = $2; total = $3; pol = $4
    if (clasif ~ /^000/ && pol == "") pol = prev_pol
    if (pol != "") prev_pol = pol
    print clasif ";" expl ";" total ";" pol
}
' /tmp/spending_with_pol.tmp > "$OUTPUT_CSV"

total_filas=$(wc -l < "$OUTPUT_CSV")
echo ""
echo "CSV generado: $OUTPUT_CSV"
echo "Total de filas: $total_filas"
echo ""
echo "Primeras 10 líneas:"
head -10 "$OUTPUT_CSV"

rm -f "$TMP_ALL" /tmp/spending_with_pol.tmp
