#!/usr/bin/env python3.10
"""
Script para construir revenue.csv a partir de ficheros CSV de presupuestos de ingresos.

Procesa ficheros CSV de los Presupuestos Generales del Estado y extrae
información de ingresos desagregados por capítulos y servicios, generando
un archivo CSV consolidado con la clasificación de ingresos.
"""

import sys
import re
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd


def normalize_amount(amount_str: str) -> float:
    """
    Normaliza una cantidad de formato español (1.234,56) a float.
    
    Args:
        amount_str: Cadena con el formato de cantidad española
        
    Returns:
        Cantidad como float (en miles de euros)
    """
    if not amount_str or not isinstance(amount_str, str):
        return 0.0
    
    # Limpiar espacios
    amount_str = amount_str.strip()
    if not amount_str:
        return 0.0
    
    # Reemplazar formato español: 1.234,56 -> 1234.56
    # Primero reemplazar puntos por nada (miles)
    amount_str = amount_str.replace('.', '')
    # Luego reemplazar comas por punto (decimales)
    amount_str = amount_str.replace(',', '.')
    
    try:
        return float(amount_str)
    except ValueError:
        return 0.0


def parse_csv_revenue_by_services(file_path: str, organismo: str) -> List[Dict]:
    """
    Parsea un archivo CSV de ingresos por servicios y capítulos.
    
    Args:
        file_path: Ruta al archivo CSV (tipo A_1.CSV con servicios y capítulos)
        organismo: Nombre del organismo (ESTADO, ORGANISMOS AUTÓNOMOS, etc)
        
    Returns:
        Lista de diccionarios con datos de ingresos
    """
    rows = []
    
    try:
        with open(file_path, 'r', encoding='windows-1252', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"Error al leer {file_path}: {e}", file=sys.stderr)
        return []
    
    # Las líneas tienen formato: Orgánica; Explicación; Cap.1; Cap.2; ... Cap.8; Total
    lines = content.split('\n')
    
    # Buscar línea de encabezado
    header_idx = None
    for i, line in enumerate(lines):
        if 'Orgánica' in line or 'Económica' in line:
            if 'Explicación' in line or 'Cap' in line:
                header_idx = i
                break
    
    if header_idx is None:
        print(f"No se encontró encabezado en {file_path}", file=sys.stderr)
        return []
    
    # Procesar filas de datos
    for i in range(header_idx + 1, len(lines)):
        line = lines[i].strip()
        if not line or line.startswith(';'):
            continue
        
        parts = [p.strip() for p in line.split(';')]
        
        if len(parts) < 3:
            continue
        
        # Saltar líneas de total
        if parts[0] == '' and 'TOTAL' in parts[1].upper():
            continue
        
        # Intentar extraer código y descripción
        codigo = parts[0] if parts[0] else ''
        descripcion = parts[1] if len(parts) > 1 else ''
        
        # Si solo tiene servicios, necesitamos descripción
        if not descripcion or len(descripcion.strip()) < 3:
            continue
        
        # Limpieza de descripción
        descripcion = descripcion.strip()
        
        # Para ESTADO, solo incluir líneas de capítulos principales (sin decimales)
        # Es decir: 1, 2, 3, 4, 5, 6, 7, 8 pero NO 98 o 98.01
        if organismo == 'ESTADO':
            # Si el código es "98" o contiene decimal, es un agregado, saltarlo
            if codigo == '98' or (codigo and '.' in codigo):
                continue
        
        # Para SEGURIDAD SOCIAL, solo incluir líneas principales (sin decimales)
        if organismo == 'SEGURIDAD SOCIAL':
            # Solo incluir código "60" (no 60.04 que es duplicado)
            if codigo and '.' in str(codigo):
                continue
        
        # Procesar capítulos (columnas 2-9 son Cap.1 a Cap.8)
        capitulos = {}
        
        for cap_idx in range(8):
            col_idx = 2 + cap_idx
            if col_idx < len(parts):
                amount = normalize_amount(parts[col_idx])
                capitulos[f"cap{cap_idx + 1}"] = amount
        
        # Obtener total (última columna)
        total = 0.0
        if len(parts) > 10:
            total = normalize_amount(parts[10])
        else:
            # Si no está en la última columna, calcular suma
            total = sum(capitulos.values())
        
        rows.append({
            'codigo': codigo,
            'descripcion': descripcion,
            'cap1': capitulos.get('cap1', 0.0),
            'cap2': capitulos.get('cap2', 0.0),
            'cap3': capitulos.get('cap3', 0.0),
            'cap4': capitulos.get('cap4', 0.0),
            'cap5': capitulos.get('cap5', 0.0),
            'cap6': capitulos.get('cap6', 0.0),
            'cap7': capitulos.get('cap7', 0.0),
            'cap8': capitulos.get('cap8', 0.0),
            'total': total,
            'organismo': organismo
        })
    
    return rows


def parse_csv_detailed_revenue_chapters(file_path: str, organismo: str) -> List[Dict]:
    """
    Parsea un archivo CSV detallado y extrae SOLO los capítulos principales (1-8).
    
    Busca líneas que comienzan con un solo dígito (1-8) o líneas de TOTAL.
    
    Args:
        file_path: Ruta al archivo CSV detallado
        organismo: Nombre del organismo
        
    Returns:
        Lista de diccionarios con los 8 capítulos principales
    """
    chapters = {}
    
    # Patrones de descripción de capítulos
    cap_patterns = {
        1: 'IMPUESTOS DIRECTOS',
        2: 'IMPUESTOS INDIRECTOS',
        3: 'TASAS, PRECIOS',
        4: 'TRANSFERENCIAS CORRIENTES',
        5: 'INGRESOS PATRIMONIALES',
        6: 'ENAJENACION',
        7: 'TRANSFERENCIAS DE CAPITAL',
        8: 'ACTIVOS FINANCIEROS',
    }
    
    try:
        with open(file_path, 'r', encoding='windows-1252', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"Error al leer {file_path}: {e}", file=sys.stderr)
        return []
    
    lines = content.split('\n')
    
    # Buscar línea de encabezado
    header_idx = None
    for i, line in enumerate(lines):
        if 'Económica' in line and 'Explicación' in line:
            header_idx = i
            break
    
    if header_idx is None:
        return []
    
    # Procesar filas de datos
    for i in range(header_idx + 1, len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        
        parts = [p.strip() for p in line.split(';')]
        
        if len(parts) < 4:
            continue
        
        codigo = parts[0]
        descripcion = parts[1] if len(parts) > 1 else ''
        
        # Buscar líneas de TOTAL para capítulos
        if codigo == '' and 'TOTAL' in descripcion:
            # Buscar el valor total (busca patrón de número)
            total_str = '0'
            for part in parts[2:]:
                # Validar si es un número: puede tener puntos (miles), comas (decimales), y signo
                if part and re.match(r'^[-+]?[\d.]+,\d+$|^[-+]?\d+$', part):
                    total_str = part
                    break
            
            amount = normalize_amount(total_str)
            
            # Identificar qué capítulo según el patrón
            for cap_num, pattern in cap_patterns.items():
                if pattern in descripcion and cap_num not in chapters:
                    chapters[cap_num] = {
                        'codigo': str(cap_num),
                        'descripcion': cap_patterns[cap_num],
                        'total': amount,
                        'organismo': organismo
                    }
                    break
    
    # Convertir a lista ordenada por capítulo
    rows = []
    for cap_num in sorted(chapters.keys()):
        rows.append(chapters[cap_num])
    
    return rows


def get_organism_name(file_code: str) -> str:
    """
    Extrae el nombre del organismo del código de archivo.
    
    Args:
        file_code: Código del archivo (ej: N_23_E_R_2_101_1 = ESTADO)
        
    Returns:
        Nombre del organismo
    """
    # Formato: N_23_E_R_2_10X_1 donde X es:
    # 1 = ESTADO, 2 = ORGANISMOS AUTÓNOMOS, 3 = RESTO DE ENTIDADES, 5 = SEGURIDAD SOCIAL
    if '_101_' in file_code:
        return 'ESTADO'
    elif '_102_' in file_code:
        return 'ORGANISMOS AUTÓNOMOS'
    elif '_103_' in file_code:
        return 'RESTO DE ENTIDADES'
    elif '_105_' in file_code:
        return 'SEGURIDAD SOCIAL'
    else:
        return 'DESCONOCIDO'


def build_revenue_dataset(pge_root: str, year: int) -> pd.DataFrame:
    """
    Construye dataset completo de ingresos desde archivos PGE.
    
    Incluye ingresos de ESTADO y SEGURIDAD SOCIAL para análisis consolidado.
    
    Args:
        pge_root: Ruta raíz de la carpeta PGE
        year: Año del presupuesto
        
    Returns:
        DataFrame con datos de ingresos consolidados
    """
    pge_path = Path(pge_root) / str(year) / 'PGE-ROM' / 'doc' / 'CSV'
    
    if not pge_path.exists():
        print(f"Ruta no encontrada: {pge_path}", file=sys.stderr)
        return pd.DataFrame()
    
    all_data = []
    
    # ESTADO: usar archivo detallado para extraer capítulos
    detailed_state_file = pge_path / 'N_23_E_R_2_101_1_2_198_1_101_1.CSV'
    if detailed_state_file.exists():
        print(f"  Procesando {detailed_state_file.name} (ESTADO - capítulos)...")
        data = parse_csv_detailed_revenue_chapters(str(detailed_state_file), 'ESTADO')
        print(f"    - {len(data)} capítulos extraídos")
        all_data.extend(data)
    
    # Otros organismos: usar archivos de servicios (A_1.CSV)
    # Nota: Para consolidado, solo incluimos SEGURIDAD SOCIAL (está en spending.csv)
    service_files = [
        # ('N_23_E_R_2_102_1_A_1.CSV', 'ORGANISMOS AUTÓNOMOS'),  # No incluir en consolidado
        # ('N_23_E_R_2_103_1_A_1.CSV', 'RESTO DE ENTIDADES'),    # No incluir en consolidado
        ('N_23_E_R_2_105_1_A_1.CSV', 'SEGURIDAD SOCIAL'),        # Incluir: gastos SS están en spending.csv
    ]
    
    for file_pattern, organism_name in service_files:
        file_path = pge_path / file_pattern
        if file_path.exists():
            print(f"  Procesando {file_pattern} ({organism_name})...")
            data = parse_csv_revenue_by_services(str(file_path), organism_name)
            print(f"    - {len(data)} filas extraídas")
            all_data.extend(data)
        else:
            print(f"  Archivo no encontrado: {file_pattern}")
    
    # Crear DataFrame
    if not all_data:
        print("No se encontraron datos", file=sys.stderr)
        return pd.DataFrame()
    
    df = pd.DataFrame(all_data)
    df['año'] = year
    
    # Reordenar columnas
    cols = ['año', 'organismo', 'codigo', 'descripcion', 'total']
    
    # Agregar capítulos si existen
    cap_cols = [col for col in df.columns if col.startswith('cap')]
    if cap_cols:
        cols.extend(sorted(cap_cols))
    
    df = df[[col for col in cols if col in df.columns]]
    
    return df


def main():
    """Función principal del script."""
    
    # Argumentos
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
    else:
        year = 2023
    
    # Rutas
    project_root = Path(__file__).parent.parent
    pge_root = project_root / 'pge'
    output_file = project_root / 'data' / 'input' / 'revenue.csv'
    
    print(f"Construyendo dataset de ingresos para el año {year}...")
    print(f"Ruta PGE: {pge_root}")
    print(f"Archivo de salida: {output_file}")
    print()
    
    # Construir dataset
    df = build_revenue_dataset(str(pge_root), year)
    
    if df.empty:
        print("Error: No se pudo construir el dataset", file=sys.stderr)
        sys.exit(1)
    
    # Guardar a CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, sep=';', encoding='utf-8', index=False, decimal=',')
    
    print(f"\nDataset guardado: {output_file}")
    print(f"Filas: {len(df)}")
    print(f"Columnas: {list(df.columns)}")
    print()
    print("Primeras filas:")
    print(df.head(10))
    
    # Validaciones
    print("\n=== VALIDACIONES ===")
    
    # Total por organismo
    print("\nTotales por organismo (miles de euros):")
    for organismo in df['organismo'].unique():
        org_data = df[df['organismo'] == organismo]
        total = org_data['total'].sum()
        print(f"  {organismo}: {total:,.2f}")
    
    # Grand total
    grand_total = df['total'].sum()
    print(f"\nGRAN TOTAL: {grand_total:,.2f} miles de euros")
    print(f"           ({grand_total * 1000:,.0f} euros)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
