#!/bin/sh
# Genera spendings.csv para el presupuesto prorrogado 2025
# Skill: build-budgets-csv

HTM_DIR="/workspace/pge/2025/PGE-ROM/doc/HTM"
POLITICAS_FILE="/workspace/politicas_gasto.txt"
OUTPUT_CSV="/workspace/spendings.csv"
TMP_ALL="/tmp/spendings_all.tmp"

rm -f "$OUTPUT_CSV" "$TMP_ALL"
echo "Generando $OUTPUT_CSV ..."

# ── Procesar cada fichero HTM ─────────────────────────────────────────────────
for htm in $(ls "$HTM_DIR"/N_24P_E_R_31_*_1_1_3_1.HTM | sort); do
    fname=$(basename "$htm")

    iconv -f windows-1252 -t utf-8 "$htm" 2>/dev/null \
      | sed 's/<span[^>]*>/\n__SPAN__/g; s/<\/span>/__ENDSPAN__\n/g' \
      | grep "__SPAN__" \
      | sed 's/^__SPAN__//; s/__ENDSPAN__$//' \
      | awk '
        # Decodifica entidades HTML numéricas.
        # Solo decodifica codepoints ASCII (<= 127); los mayores se dejan como texto
        # (el fichero ya viene en UTF-8 via iconv, los &#NNN; > 127 son redundantes)
        function decode(s,    result, code, chunk) {
            result = ""
            while (length(s) > 0) {
                if (match(s, /&#[0-9]+;/)) {
                    result = result substr(s, 1, RSTART-1)
                    code = substr(s, RSTART+2, RLENGTH-3) + 0
                    if (code <= 127) {
                        result = result sprintf("%c", code)
                    } else {
                        # Para codepoints > 127 usamos la representación UTF-8 del fichero:
                        # eliminamos la entidad y dejamos vacío (el char real ya estará
                        # en el texto literal gracias al iconv)
                        # En estos ficheros solo las letras con tilde se codifican así
                        # y el texto literal ya no está: todo es entidad. 
                        # Necesitamos producir el char UTF-8 manualmente.
                        if (code == 193) result = result "\xC3\x81"   # Á
                        else if (code == 201) result = result "\xC3\x89"  # É
                        else if (code == 205) result = result "\xC3\x8D"  # Í
                        else if (code == 211) result = result "\xC3\x93"  # Ó
                        else if (code == 218) result = result "\xC3\x9A"  # Ú
                        else if (code == 225) result = result "\xC3\xA1"  # á
                        else if (code == 233) result = result "\xC3\xA9"  # é
                        else if (code == 237) result = result "\xC3\xAD"  # í
                        else if (code == 243) result = result "\xC3\xB3"  # ó
                        else if (code == 250) result = result "\xC3\xBA"  # ú
                        else if (code == 241) result = result "\xC3\xB1"  # ñ
                        else if (code == 209) result = result "\xC3\x91"  # Ñ
                        else if (code == 252) result = result "\xC3\xBC"  # ü
                        else if (code == 231) result = result "\xC3\xA7"  # ç
                        else if (code == 191) result = result "\xC2\xBF"  # ¿
                        else if (code == 161) result = result "\xC2\xA1"  # ¡
                        else if (code == 186) result = result "\xC2\xBA"  # º
                        else if (code == 170) result = result "\xC2\xAA"  # ª
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

        BEGIN {
            found_header = 0
            ncols = 0
            buf_count = 0
            seccion = ""
            counting_header = 0
            header_count = 0
        }

        {
            decoded = decode($0)
        }

        # Capturar sección: línea que contiene el patrón de sección
        !found_header && (decoded ~ /Secci/ || $0 ~ /&#243;n/) && decoded !~ /Clasif/ {
            if (match(decoded, /: /)) {
                seccion = substr(decoded, RSTART + 2)
                gsub(/^[[:space:]]+|[[:space:]]+$/, "", seccion)
            } else if (match($0, /&#58; /)) {
                # Fallback: extraer del raw y decodificar solo ASCII
                rest = substr($0, RSTART + 6)
                seccion = decode(rest)
                gsub(/^[[:space:]]+|[[:space:]]+$/, "", seccion)
            }
        }

        # Detectar inicio del header
        !found_header && decoded ~ /^Clasif\./ {
            counting_header = 1
            header_count = 1
            next
        }

        # Contar columnas del header hasta "Total"
        counting_header && !found_header {
            header_count++
            if (decoded == "Total") {
                ncols = header_count
                found_header = 1
                counting_header = 0
                buf_count = 0
            }
            next
        }

        # Acumular datos en grupos de ncols
        found_header && ncols > 0 {
            buf[buf_count] = decoded
            buf_count++

            if (buf_count == ncols) {
                clasif = buf[0]
                expl   = buf[1]
                total  = buf[ncols - 1]
                buf_count = 0

                # Validar código: 3 dígitos + 1 alfanum
                if (clasif !~ /^[0-9][0-9][0-9][A-Za-z0-9]$/) next

                # Excluir filas de totales
                if (expl ~ /^TOTAL/) next

                # Excluir sin importe
                if (total == "") next

                # Añadir sección a códigos 000X
                if (clasif ~ /^000/) {
                    expl = expl " (Sección: " seccion ")"
                }

                print clasif "|" expl "|" total
            }
        }
      ' >> "$TMP_ALL"

    count=$(wc -l < "$TMP_ALL" 2>/dev/null || echo 0)
    echo "  $fname procesado (acumulado: $count filas)"
done

total_raw=$(wc -l < "$TMP_ALL")
echo ""
echo "Líneas extraídas en bruto: $total_raw"

# ── Cruzar con políticas de gasto ────────────────────────────────────────────
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

# ── Política más frecuente (para 000X) ───────────────────────────────────────
politica_frecuente=$(awk -F'|' '
$1 !~ /^000/ && $4 != "" { count[$4]++ }
END {
    max = 0; best = ""
    for (p in count) { if (count[p] > max) { max = count[p]; best = p } }
    print best
}
' /tmp/spendings_with_pol.tmp)

echo "Política más frecuente (para 000X): $politica_frecuente"

# ── Escribir CSV final ────────────────────────────────────────────────────────
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
echo ""
echo "Filas 000X:"
grep "^000X" "$OUTPUT_CSV"

rm -f "$TMP_ALL" /tmp/spendings_with_pol.tmp
