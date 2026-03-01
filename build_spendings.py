#!/usr/bin/env python3
"""
Genera spendings.csv a partir de los ficheros HTM del presupuesto prorrogado 2025.
Skill: build-budgets-csv
"""

import os
import re
import glob
from html.parser import HTMLParser
from collections import Counter


# ── Configuración ─────────────────────────────────────────────────────────────
HTM_DIR = "/workspace/pge/2025/PGE-ROM/doc/HTM"
POLITICAS_FILE = "/workspace/politicas_gasto.txt"
OUTPUT_CSV = "/workspace/spendings.csv"

HTM_PATTERN = os.path.join(HTM_DIR, "N_24P_E_R_31_*_1_1_3_1.HTM")


# ── Parser HTML ───────────────────────────────────────────────────────────────
class TableParser(HTMLParser):
    """Extrae el texto de cada <span> dentro del documento."""

    def __init__(self):
        super().__init__()
        self.spans = []
        self._in_span = False
        self._current = []

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            self._in_span = True
            self._current = []

    def handle_endtag(self, tag):
        if tag == "span" and self._in_span:
            self.spans.append("".join(self._current).strip())
            self._in_span = False

    def handle_data(self, data):
        if self._in_span:
            self._current.append(data)

    def handle_charref(self, name):
        if self._in_span:
            try:
                if name.startswith("x"):
                    char = chr(int(name[1:], 16))
                else:
                    char = chr(int(name))
                self._current.append(char)
            except (ValueError, OverflowError):
                pass


# ── Carga de políticas de gasto ───────────────────────────────────────────────
def load_politicas(path: str) -> dict:
    """Devuelve un dict: prefijo_2_chars -> texto_completo_politica."""
    politicas = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                prefix = line[:2]
                politicas[prefix] = line
    return politicas


# ── Extracción de nombre de sección ──────────────────────────────────────────
SECCION_RE = re.compile(r"Secci[oó]n[:\s]+(.+)", re.IGNORECASE)


def extract_seccion(spans: list) -> str:
    for s in spans:
        m = SECCION_RE.search(s)
        if m:
            return m.group(1).strip()
    return ""


# ── Código de programa válido ─────────────────────────────────────────────────
PROG_RE = re.compile(r"^[0-9]{3}[A-Za-z0-9]$")

TOTALES_KEYWORDS = {"TOTAL"}


# ── Parseo de un fichero HTM ──────────────────────────────────────────────────
def parse_htm(filepath: str, politicas: dict):
    """Devuelve una lista de tuplas (codigo, descripcion, total, politica)."""
    with open(filepath, encoding="windows-1252", errors="replace") as f:
        content = f.read()

    parser = TableParser()
    parser.feed(content)
    spans = parser.spans

    seccion = extract_seccion(spans)

    # Localizar inicio de la tabla de datos buscando el header
    header_idx = None
    for i, s in enumerate(spans):
        if "Clasif" in s and "programas" in s:
            header_idx = i
            break

    if header_idx is None:
        return []

    # Los datos vienen en grupos de 5 spans (una fila = 5 celdas)
    data_spans = spans[header_idx + 5:]

    rows = []
    i = 0
    while i + 4 < len(data_spans):
        clasif = data_spans[i].strip()
        expl   = data_spans[i + 1].strip()
        total  = data_spans[i + 4].strip()
        i += 5

        # Filtrar filas sin código válido
        if not clasif or not PROG_RE.match(clasif):
            continue
        # Filtrar filas de totales
        if any(kw in expl.upper() for kw in TOTALES_KEYWORDS):
            continue
        # Filtrar filas sin importe
        if not total:
            continue

        # Para códigos 000X añadir sección a la descripción
        if clasif.startswith("000"):
            expl = f"{expl} (Sección: {seccion})"

        # Determinar política de gasto por los 2 primeros caracteres
        prefix = clasif[:2]
        politica = politicas.get(prefix, "")

        rows.append((clasif, expl, total, politica))

    return rows


# ── Función principal ─────────────────────────────────────────────────────────
def main():
    # Borrar CSV si existe
    if os.path.exists(OUTPUT_CSV):
        os.remove(OUTPUT_CSV)
        print(f"Borrado fichero previo: {OUTPUT_CSV}")

    politicas = load_politicas(POLITICAS_FILE)
    print(f"Políticas de gasto cargadas: {len(politicas)}")

    ficheros = sorted(glob.glob(HTM_PATTERN))
    print(f"Ficheros HTM a procesar: {len(ficheros)}")

    all_rows = []
    for fpath in ficheros:
        fname = os.path.basename(fpath)
        rows = parse_htm(fpath, politicas)
        print(f"  {fname}: {len(rows)} filas")
        all_rows.extend(rows)

    # Política más frecuente (para asignar a códigos 000X sin match)
    non_000_politicas = [r[3] for r in all_rows if not r[0].startswith("000") and r[3]]
    politica_mas_frecuente = ""
    if non_000_politicas:
        counter = Counter(non_000_politicas)
        politica_mas_frecuente = counter.most_common(1)[0][0]
        print(f"\nPolítica más frecuente (para 000X): {politica_mas_frecuente}")

    # Sustituir política vacía en filas 000X
    final_rows = []
    for clasif, expl, total, politica in all_rows:
        if clasif.startswith("000") and not politica:
            politica = politica_mas_frecuente
        final_rows.append((clasif, expl, total, politica))

    # Escribir CSV
    with open(OUTPUT_CSV, "w", encoding="utf-8") as f:
        for clasif, expl, total, politica in final_rows:
            f.write(f"{clasif};{expl};{total};{politica}\n")

    print(f"\nCSV generado: {OUTPUT_CSV}")
    print(f"Total de filas: {len(final_rows)}")

    print("\nPrimeras 10 líneas:")
    for row in final_rows[:10]:
        print("  " + ";".join(row))


if __name__ == "__main__":
    main()
