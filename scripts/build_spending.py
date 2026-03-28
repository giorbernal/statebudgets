#!/usr/bin/env python3.10
"""
Script para construir spending.csv a partir de ficheros HTM de presupuestos.

Procesa ficheros HTML de los Presupuestos Generales del Estado y extrae
información de gastos por programas, generando un archivo CSV con la
clasificación de gastos.
"""

import sys
import os
import re
import glob
import html
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def load_politicas_gasto() -> Dict[str, str]:
    """
    Carga el archivo politicas_gasto.txt y crea un diccionario.
    
    Returns:
        Diccionario con las dos primeras letras del código como clave
        y la política como valor.
    """
    politicas = {}
    # Usar ruta relativa al directorio raíz del proyecto
    project_root = Path(__file__).parent.parent
    politicas_file = project_root / "scripts" / "politicas_gasto.txt"
    
    try:
        with open(politicas_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Format: "NN. DESCRIPCIÓN"
                parts = line.split('. ', 1)
                if len(parts) == 2:
                    codigo_dos_digitos = parts[0].strip()
                    descripcion = f"{line.split('. ', 1)[0]}. {parts[1]}"
                    # Extraer solo los dos primeros caracteres del código
                    if len(codigo_dos_digitos) >= 2:
                        key = codigo_dos_digitos[:2]
                        politicas[key] = descripcion
    except FileNotFoundError:
        print(f"Error: Archivo {politicas_file} no encontrado", file=sys.stderr)
        sys.exit(1)
    
    return politicas


def parse_htm_file(file_path: str) -> List[Tuple[str, str, str, Optional[str]]]:
    """
    Parsea un archivo HTM y extrae las filas con "Clasif. por programas".
    
    Soporta dos formatos:
    - 2014-2026: Usa etiquetas <span>
    - 2011-2013: Usa etiquetas <div>
    
    Args:
        file_path: Ruta al archivo HTM
        
    Returns:
        Lista de tuplas (código, descripción, importe, sección)
    """
    try:
        with open(file_path, 'r', encoding='windows-1252') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error al leer {file_path}: {e}", file=sys.stderr)
            return []
    
    # Decodificar entidades HTML
    content = html.unescape(content)
    
    # Extraer información de sección
    section_match = re.search(r'Sección:\s*(\d+\s+[^<]+)', content, re.IGNORECASE)
    section = section_match.group(1).strip() if section_match else None
    
    # Intentar extraer spans primero (formato 2014+)
    elements = re.findall(r'<span[^>]*>([^<]+)</span>', content, re.IGNORECASE)
    
    # Si no hay spans, intentar DIVs (formato 2011-2013)
    if not elements:
        elements = re.findall(r'<div[^>]*>([^<]+)</div>', content, re.IGNORECASE)
    
    rows = []
    
    # Encontrar el índice donde comienza "Clasif. por programas"
    clasif_idx = None
    for i, element in enumerate(elements):
        if "Clasif" in element and "programas" in element:
            clasif_idx = i
            break
    
    if clasif_idx is None:
        return rows
    
    # Encontrar el índice de la columna "Total" en los headers
    total_col_idx = find_total_column_index(elements, clasif_idx)
    
    # Calcular el offset del header "Total" respecto a "Clasif. por programas"
    header_offset = total_col_idx - clasif_idx if total_col_idx != -1 else -1
    
    # Saltar los encabezados de la tabla (buscar el primer código válido)
    i = clasif_idx + 5
    
    # Saltar hasta encontrar el primer código válido
    while i < len(elements):
        element = elements[i].strip()
        if (len(element) >= 3 and len(element) <= 4 and 
            all(c.isalnum() for c in element) and 
            not element.isdigit()):
            break
        i += 1
    
    # Procesar filas hasta encontrar "TOTAL" o fin del documento
    while i < len(elements):
        element = elements[i].strip()
        
        # Parar si llegamos a encabezados de totales o secciones
        if "TOTAL" in element.upper() or "CONSOLIDADO" in element.upper():
            break
        
        # Verificar si es un código (3-4 caracteres alfanuméricos)
        if (len(element) >= 3 and len(element) <= 4 and 
            all(c.isalnum() for c in element) and 
            not element.isdigit()):
            
            code = element
            
            # Obtener descripción (siguiente elemento)
            if i + 1 < len(elements):
                desc = elements[i + 1].strip()
            else:
                i += 1
                continue
            
            # Obtener importe de la columna "Total"
            # Estrategia principal: buscar el último valor numérico antes del siguiente código
            # Esto funciona independientemente del número de columnas en cada fila
            amount = None
            j = i + 2
            last_numeric = None
            while j < len(elements):
                candidate = elements[j].strip()
                # Parar si encontramos el siguiente código o TOTAL
                if (len(candidate) >= 3 and len(candidate) <= 4 and 
                    all(c.isalnum() for c in candidate) and 
                    not candidate.isdigit()):
                    break
                if "TOTAL" in candidate.upper():
                    break
                # Verificar si es un importe válido
                if any(c.isdigit() for c in candidate) and (',' in candidate or '.' in candidate):
                    # Guardar el último valor numérico encontrado (más probable que sea Total)
                    last_numeric = candidate
                j += 1
            if last_numeric:
                amount = last_numeric
            
            # Fallback: usar offset de cabecera si no se encontró amount
            if amount is None and header_offset != -1:
                total_amount_idx = i + header_offset
                if total_amount_idx < len(elements):
                    candidate = elements[total_amount_idx].strip()
                    is_code = (len(candidate) >= 3 and len(candidate) <= 4 and 
                               all(c.isalnum() for c in candidate) and 
                               not candidate.isdigit())
                    if (any(c.isdigit() for c in candidate) and 
                        (',' in candidate or '.' in candidate) and
                        not is_code):
                        amount = candidate
            
            if amount and desc and "TOTAL" not in desc.upper() and "CONSOLIDADO" not in desc.upper():
                rows.append((code, desc, amount, section))
            
            # Avanzar al siguiente código - buscar directamente el siguiente código válido
            j = i + 1
            next_code_found = False
            while j < len(elements):
                elem = elements[j].strip()
                if (len(elem) >= 3 and len(elem) <= 4 and 
                    all(c.isalnum() for c in elem) and 
                    not elem.isdigit() and 
                    "TOTAL" not in elem.upper() and 
                    "CONSOLIDADO" not in elem.upper()):
                    i = j
                    next_code_found = True
                    break
                j += 1
            if not next_code_found:
                i += 1
        else:
            i += 1
    
    return rows


def find_total_column_index(elements: List[str], clasif_idx: int) -> int:
    """
    Encuentra el índice de la columna 'Total' en los headers de la tabla.
    
    Args:
        elements: Lista de elementos extraídos del HTML
        clasif_idx: Índice de "Clasif. por programas"
        
    Returns:
        Índice absoluto de 'Total' en elements, o -1 si no encuentra
    """
    # Los headers están entre "Clasif. por programas" y el primer código
    # Buscar "Total" en los headers (típicamente dentro de los próximos 15 elementos)
    for i in range(clasif_idx, min(clasif_idx + 15, len(elements))):
        if elements[i].strip().upper() == "TOTAL":
            return i
    return -1



def find_proroga_file(year: int, project_root: Path) -> Optional[str]:
    """
    Busca el fichero de prórroga (*31_*G_1_3_1.HTM o *31_*G_1_7.HTM) para el año.
    Si no existe en el año actual, busca recursivamente en años anteriores.
    
    Razonamiento: Si el fichero de prórroga no existe en el año solicitado,
    significa que ese año usa la prórroga del año anterior. Si tampoco existe
    en el año anterior, continúa buscando en años anteriores hasta encontrarlo.
    
    Args:
        year: Año a procesar
        project_root: Ruta raíz del proyecto
        
    Returns:
        Ruta del fichero de prórroga encontrado, o None si no existe
    """
    if year < 2011:
        return None
    
    base_dir = project_root / "pge" / str(year) / "PGE-ROM" / "doc" / "HTM"
    
    if not base_dir.exists():
        return None
    
    # Determinar patrón según el año
    if year > 2013:
        pattern = "N_*_E_R_31_*G_1_3_1.HTM"
    else:
        pattern = "N_*_E_R_31_*G_1_7.HTM"
    
    # Buscar el fichero
    file_paths = glob.glob(str(base_dir / pattern))
    
    if file_paths:
        # Retornar el primer fichero encontrado
        return file_paths[0]
    
    # Si no existe, buscar en el año anterior
    print(f"Fichero de prórroga no encontrado para {year}, buscando en {year - 1}...")
    return find_proroga_file(year - 1, project_root)


def build_spending_csv(year: int):
    """
    Construye el archivo spending.csv para un año específico.
    
    Args:
        year: Año a procesar (2011-2026)
    """
    # Validar año
    if year < 2011 or year > 2026:
        print(f"Error: Año {year} fuera de rango (2011-2026)", file=sys.stderr)
        sys.exit(1)
    
    # Rutas relativas al directorio raíz del proyecto
    project_root = Path(__file__).parent.parent
    base_dir = project_root / "pge" / str(year) / "PGE-ROM" / "doc" / "HTM"
    output_file = project_root / "pge" / str(year) / "spending.csv"
    
    # Verificar que la ruta base existe
    if not base_dir.exists():
        print(f"Error: Ruta no encontrada: {base_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Limpiar archivo anterior si existe
    if output_file.exists():
        output_file.unlink()
        print(f"Archivo anterior eliminado: {output_file}")
    
    # Cargar políticas de gasto
    politicas = load_politicas_gasto()
    
    # Determinar patrones de búsqueda
    if year > 2013:
        # Patrones para años > 2013
        year_suffix = str(year)[-2:]
        prev_year_suffix = str(year - 1)[-2:]
        patterns = [
            f"N_{prev_year_suffix}P_E_R_31_*_1_1_3_1.HTM",
            f"N_{year_suffix}_E_R_31_*_1_1_3_1.HTM",
        ]
    else:
        # Patrones para años <= 2013
        # Nota: El patrón especificado es __1_1_7 pero en archivos reales puede ser _1_1_7
        year_suffix = str(year)[-2:]
        prev_year_suffix = str(year - 1)[-2:]
        patterns = [
            f"N_{prev_year_suffix}P_E_R_31_*_1_1_7.HTM",
            f"N_{year_suffix}_E_R_31_*_1_1_7.HTM"
        ]
    
    # Buscar y procesar archivos
    all_rows = []
    files_processed = 0
    
    for pattern in patterns:
        file_paths = glob.glob(str(base_dir / pattern))
        
        for file_path in file_paths:
            print(f"Procesando: {file_path}")
            rows = parse_htm_file(file_path)
            all_rows.extend(rows)
            files_processed += 1
    
    # Buscar y procesar fichero de prórroga (*31_*G_1_3_1.HTM o *31_*G_1_7.HTM)
    # Solo se procesa si se encontraron archivos normales (no es una prórroga completa)
    proroga_file = find_proroga_file(year, project_root)
    if proroga_file:
        print(f"Procesando fichero de prórroga: {proroga_file}")
        rows = parse_htm_file(proroga_file)
        all_rows.extend(rows)
        files_processed += 1
    
    if files_processed == 0:
        print(f"Advertencia: No se encontraron archivos para {year}", file=sys.stderr)
        return
    
    # Procesamos las filas para agregar la política
    final_rows = []
    last_policy = None
    
    for row in all_rows:
        if len(row) == 3:
            code, desc, amount = row
            section = None
        else:
            code, desc, amount, section = row
        
        # Obtener los dos primeros caracteres del código
        code_prefix = code[:2] if len(code) >= 2 else code
        
        # Buscar política
        if code_prefix == "00":
            # Usar la política anterior para códigos 00
            policy = last_policy
            # Agregar sección al nombre si es código 000x
            if section:
                desc = f"{desc} (Sección: {section})"
        else:
            policy = politicas.get(code_prefix, "")
            last_policy = policy
        
        final_rows.append((code, desc, amount, policy))
    
    # Escribir archivo CSV
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for code, desc, amount, policy in final_rows:
                f.write(f"{code};{desc};{amount};{policy}\n")
        
        print(f"\nArchivo generado: {output_file}")
        print(f"Total de registros: {len(final_rows)}")
        
    except Exception as e:
        print(f"Error al escribir {output_file}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Función principal."""
    if len(sys.argv) != 2:
        print("Uso: python3.10 build_spending.py <año>")
        print("Ejemplo: python3.10 build_spending.py 2026")
        sys.exit(1)
    
    try:
        year = int(sys.argv[1])
    except ValueError:
        print(f"Error: {sys.argv[1]} no es un año válido", file=sys.stderr)
        sys.exit(1)
    
    build_spending_csv(year)


if __name__ == "__main__":
    main()
