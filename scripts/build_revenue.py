#!/usr/bin/env python3.10
"""
Script para construir revenue.csv a partir de ficheros de presupuestos de ingresos.

Procesa múltiples formatos:
- CSV clásico (2017-2023): Archivos N_XX_E_R_2_*_7_A_1.CSV
- HTML (2011-2016): Archivos N_XX_E_R_2_*_7_A_1.HTM
- CSV nuevo (2024-2026): Archivos N_*P_E_V_1_* con nueva estructura

Genera un archivo CSV consolidado con clasificación de ingresos por capítulos.

Características:
- Soporta múltiples años (2011-2026) con diferentes formatos
- Usa parsers específicos por formato de archivo
- Consolida ESTADO + SEGURIDAD SOCIAL
"""

import sys
import re
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd

# Importar parsers independientes
from revenue_parsers import (
    build_revenue_html_format,
    build_revenue_new_format,
)


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
    
    amount_str = amount_str.strip()
    if not amount_str:
        return 0.0
    
    # Reemplazar formato español: 1.234,56 -> 1234.56
    amount_str = amount_str.replace('.', '')
    amount_str = amount_str.replace(',', '.')
    
    try:
        return float(amount_str)
    except ValueError:
        return 0.0


def find_revenue_files(pge_year_path: Path, year: int) -> Dict[str, Path]:
    """
    Busca archivos de ingresos en una carpeta de año específico.
    
    Soporta múltiples patrones de nombres de archivo según el año.
    
    Args:
        pge_year_path: Ruta a la carpeta del año
        year: Año del presupuesto
        
    Returns:
        Dict con rutas a archivos por organismo
    """
    files = {
        'estado_chapters': None,
        'estado_services': None,
        'seguridad_social_services': None,
    }
    
    # Búsqueda flexible de archivos CSV
    csv_path = pge_year_path / 'doc' / 'CSV'
    if csv_path.exists():
        # Buscar archivos de ESTADO por servicios (*2_101_1_A_1.CSV)
        for f in csv_path.glob('*2_101_1_A_1.CSV'):
            files['estado_services'] = f
            break
        
        # Buscar archivos de ESTADO por capítulos (*2_101_1_7_A_1.CSV)
        for f in csv_path.glob('*2_101_1_7_A_1.CSV'):
            files['estado_chapters'] = f
            break
        
        # Buscar archivos de SEGURIDAD SOCIAL (*2_105_1_A_1.CSV)
        for f in csv_path.glob('*2_105_1_A_1.CSV'):
            files['seguridad_social_services'] = f
            break
    
    return files


def parse_csv_revenue_by_services(file_path: Path, organismo: str) -> List[Dict]:
    """
    Parsea un archivo CSV de ingresos por servicios y capítulos.
    
    Args:
        file_path: Ruta al archivo CSV
        organismo: Nombre del organismo
        
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
    
    lines = content.split('\n')
    
    # Buscar línea de encabezado
    header_idx = None
    for i, line in enumerate(lines):
        if 'Orgánica' in line or 'Económica' in line:
            if 'Explicación' in line or 'Cap' in line:
                header_idx = i
                break
    
    if header_idx is None:
        return []
    
    # Procesar filas de datos
    for i in range(header_idx + 1, len(lines)):
        line = lines[i].strip()
        if not line or line.startswith(';'):
            continue
        
        parts = [p.strip() for p in line.split(';')]
        
        if len(parts) < 3:
            continue
        
        codigo = parts[0] if parts[0] else ''
        descripcion = parts[1] if len(parts) > 1 else ''
        
        # Saltar líneas de total
        if parts[0] == '' and 'TOTAL' in parts[1].upper():
            continue
        
        if not descripcion or len(descripcion.strip()) < 3:
            continue
        
        descripcion = descripcion.strip()
        
        # Para ESTADO, solo incluir línea 98 (sin decimales) como resumen de capítulos
        if organismo == 'ESTADO':
            # Solo aceptar código '98' sin decimales (es el total consolidado)
            if codigo == '98':
                # OK, mantener
                pass
            else:
                # Rechazar todo lo demás (99, 98.01, etc.)
                continue
        
        # Para SEGURIDAD SOCIAL, solo incluir línea 60 (sin decimales)
        if organismo == 'SEGURIDAD SOCIAL':
            # Solo aceptar código '60' sin decimales
            if codigo == '60':
                # OK, mantener
                pass
            else:
                # Rechazar todo lo demás (60.04, etc.)
                continue
        
        # Procesar capítulos
        capitulos = {}
        
        for cap_idx in range(8):
            col_idx = 2 + cap_idx
            if col_idx < len(parts):
                amount = normalize_amount(parts[col_idx])
                capitulos[f"cap{cap_idx + 1}"] = amount
        
        # Obtener total (última columna no vacía)
        total = 0.0
        if len(parts) > 10:
            total = normalize_amount(parts[10])
        else:
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


def parse_csv_chapters_simple(file_path: Path, organismo: str) -> List[Dict]:
    """
    Parsea un archivo CSV simple con capítulos (3 columnas: Económica, Explicación, Total).
    
    Este es el formato del archivo 7_A_1 (resumen por capítulos).
    
    Args:
        file_path: Ruta al archivo CSV
        organismo: Nombre del organismo
        
    Returns:
        Lista de diccionarios con los capítulos
    """
    rows = []
    
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
    
    # Procesar filas de datos - solo capítulos 1-8
    for i in range(header_idx + 1, len(lines)):
        line = lines[i].strip()
        if not line or line.startswith(';'):
            continue
        
        parts = [p.strip() for p in line.split(';')]
        if len(parts) < 3:
            continue
        
        codigo = parts[0]
        descripcion = parts[1]
        total_str = parts[2]
        
        # Solo aceptar códigos de un dígito (1-8)
        if codigo and codigo.isdigit() and int(codigo) <= 8:
            amount = normalize_amount(total_str)
            rows.append({
                'codigo': codigo,
                'descripcion': descripcion.strip(),
                'total': amount,
                'organismo': organismo,
                'cap1': 0.0, 'cap2': 0.0, 'cap3': 0.0, 'cap4': 0.0,
                'cap5': 0.0, 'cap6': 0.0, 'cap7': 0.0, 'cap8': 0.0,
            })
    
    return rows


def parse_csv_detailed_revenue_chapters(file_path: Path, organismo: str) -> List[Dict]:
    """
    Parsea un archivo CSV detallado y extrae los capítulos principales (1-8).
    
    Args:
        file_path: Ruta al archivo CSV detallado
        organismo: Nombre del organismo
        
    Returns:
        Lista de diccionarios con los capítulos principales
    """
    chapters = {}
    
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
        
        # Buscar el valor total (puede estar en parts[3] o en algún otro lugar no vacío)
        total_str = '0'
        for part in parts[2:]:
            if part and re.match(r'^[-+]?[\d.]+,\d+$|^[-+]?\d+$', part):
                total_str = part
                break
        
        amount = normalize_amount(total_str)
        
        # Buscar líneas de TOTAL para capítulos
        if codigo == '' and 'TOTAL' in descripcion:
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


def build_revenue_dataset_for_year(pge_root: str, year: int, 
                                   previous_descriptions: Optional[Dict] = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Construye dataset de ingresos para un año específico.
    
    Args:
        pge_root: Ruta raíz de la carpeta PGE
        year: Año del presupuesto
        previous_descriptions: Descripciones del año anterior (para usar como fallback)
        
    Returns:
        Tupla (DataFrame, Dict con descripciones del año para el siguiente)
    """
    pge_year_path = Path(pge_root) / str(year) / 'PGE-ROM'
    
    if not pge_year_path.exists():
        print(f"⚠ Año {year}: Directorio no encontrado", file=sys.stderr)
        return pd.DataFrame(), {}
    
    all_data = []
    current_descriptions = {}
    
    # Buscar archivos disponibles
    files = find_revenue_files(pge_year_path, year)
    
    # ESTADO: primero intentar con archivo de capítulos, luego con servicios
    if files['estado_chapters']:
        print(f"  Procesando {files['estado_chapters'].name} (ESTADO - capítulos)...")
        data = parse_csv_chapters_simple(files['estado_chapters'], 'ESTADO')
        print(f"    ✓ {len(data)} capítulos extraídos")
        all_data.extend(data)
        
        # Guardar descripciones
        for row in data:
            current_descriptions[f"ESTADO_{row['codigo']}"] = row['descripcion']
    elif files['estado_services']:
        print(f"  Procesando {files['estado_services'].name} (ESTADO - servicios)...")
        data = parse_csv_revenue_by_services(files['estado_services'], 'ESTADO')
        print(f"    ✓ {len(data)} servicios extraídos")
        all_data.extend(data)
        
        # Guardar descripciones
        for row in data:
            current_descriptions[f"ESTADO_{row['codigo']}"] = row['descripcion']
    else:
        print(f"  ⚠ Año {year}: No se encontraron archivos de ESTADO")
    
    # SEGURIDAD SOCIAL
    if files['seguridad_social_services']:
        print(f"  Procesando {files['seguridad_social_services'].name} (SEGURIDAD SOCIAL)...")
        data = parse_csv_revenue_by_services(files['seguridad_social_services'], 'SEGURIDAD SOCIAL')
        print(f"    ✓ {len(data)} filas extraídas")
        all_data.extend(data)
        
        # Guardar descripciones
        for row in data:
            current_descriptions[f"SS_{row['codigo']}"] = row['descripcion']
    else:
        print(f"  ⚠ Año {year}: No se encontraron archivos de SEGURIDAD SOCIAL")
    
    # Si no hay datos, retornar vacío
    if not all_data:
        print(f"⚠ Año {year}: No se extrajeron datos", file=sys.stderr)
        return pd.DataFrame(), current_descriptions
    
    # Crear DataFrame
    df = pd.DataFrame(all_data)
    df['año'] = year
    
    # Aplicar descripciones del año anterior si las actuales están vacías
    if previous_descriptions:
        for idx, row in df.iterrows():
            key = f"{row['organismo']}_{row['codigo']}"
            if not row['descripcion'] or row['descripcion'].strip() == '':
                if key in previous_descriptions:
                    df.at[idx, 'descripcion'] = previous_descriptions[key]
                    print(f"    → Usando descripción del año anterior para {key}")
    
    # Reordenar columnas
    cols = ['año', 'organismo', 'codigo', 'descripcion', 'total']
    cap_cols = [col for col in df.columns if col.startswith('cap')]
    if cap_cols:
        cols.extend(sorted(cap_cols))
    
    df = df[[col for col in cols if col in df.columns]]
    
    return df, current_descriptions


def detect_and_build_for_year(pge_root: str, year: int) -> pd.DataFrame:
    """
    Detecta el formato disponible para un año y usa el parser apropiado.
    
    Prioridad:
    1. CSV clásico (N_XX_E_R_2_*_7_A_1.CSV) - 2017-2023
    2. HTML (N_XX_E_R_2_*_7_A_1.HTM) - 2011-2016
    3. CSV nuevo (N_*P_E_V_1_*) - 2024-2026
    4. build_revenue_dataset_for_year (fallback original)
    
    Args:
        pge_root: Ruta raíz de carpeta PGE
        year: Año del presupuesto
        
    Returns:
        DataFrame con datos de ingresos, vacío si no hay datos disponibles
    """
    pge_year_path = Path(pge_root) / str(year) / 'PGE-ROM'
    csv_path = pge_year_path / 'doc' / 'CSV'
    htm_path = pge_year_path / 'doc' / 'HTM'
    
    # 1. Intentar con CSV clásico (2017-2023)
    if csv_path.exists():
        classic_csv_exists = len(list(csv_path.glob('*_E_R_2_*_7_A_1.CSV'))) > 0
        if classic_csv_exists:
            print(f"  → Usando formato CSV clásico")
            df, _ = build_revenue_dataset_for_year(pge_root, year)
            return df
    
    # 2. Intentar con HTML (2011-2016)
    if htm_path.exists():
        html_file_exists = len(list(htm_path.glob('*_E_R_2_*_7_A_1.HTM'))) > 0
        if html_file_exists:
            print(f"  → Usando formato HTML")
            df = build_revenue_html_format(pge_root, year)
            return df
    
    # 3. Intentar con CSV nuevo (2024-2026)
    if csv_path.exists():
        new_csv_exists = len(list(csv_path.glob('*_E_V_1_*.CSV'))) > 0
        if new_csv_exists:
            print(f"  → Usando formato CSV nuevo")
            df = build_revenue_new_format(pge_root, year)
            return df
    
    # 4. Fallback (original)
    print(f"  → Intento fallback (formato original)")
    df, _ = build_revenue_dataset_for_year(pge_root, year)
    return df


def main():
    """Función principal del script."""
    
    # Argumentos
    if len(sys.argv) > 1:
        year_arg = sys.argv[1]
        if year_arg == 'all':
            years = list(range(2011, 2027))
        else:
            try:
                years = [int(year_arg)]
            except ValueError:
                print("Uso: python build_revenue.py <año|all>", file=sys.stderr)
                sys.exit(1)
    else:
        years = [2023]
    
    # Rutas
    project_root = Path(__file__).parent.parent
    pge_root = project_root / 'pge'
    output_file = project_root / 'data' / 'input' / 'revenue.csv'
    
    print(f"Construyendo dataset de ingresos para años: {years}")
    print(f"Ruta PGE: {pge_root}")
    print()
    
    # Procesar múltiples años
    all_dfs = []
    
    for year in years:
        print(f"=== Procesando año {year} ===")
        df = detect_and_build_for_year(str(pge_root), year)
        
        if not df.empty:
            all_dfs.append(df)
            
            total_ingresos = df['total'].sum()
            print(f"✓ Año {year}: {total_ingresos:,.2f} miles €")
        else:
            print(f"✗ Año {year}: Sin datos disponibles")
        print()
    
    # Consolidar todos los años
    if not all_dfs:
        print("Error: No se pudieron procesar ningún año", file=sys.stderr)
        sys.exit(1)
    
    consolidated_df = pd.concat(all_dfs, ignore_index=True)
    
    # Guardar a CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    consolidated_df.to_csv(output_file, sep=';', encoding='utf-8', index=False, decimal=',')
    
    print(f"\n{'='*70}")
    print(f"Dataset guardado: {output_file}")
    print(f"Total de filas: {len(consolidated_df)}")
    print(f"Años procesados: {sorted(consolidated_df['año'].unique().tolist())}")
    print(f"Columnas: {list(consolidated_df.columns)}")
    
    # Resumen por año
    print(f"\n{'='*70}")
    print("Totales por año (miles de euros):")
    yearly_totals = consolidated_df.groupby('año')['total'].sum().sort_index()
    for year, total in yearly_totals.items():
        print(f"  {year}: {total:>15,.2f}")
    
    grand_total = consolidated_df['total'].sum()
    print(f"\nGRAN TOTAL (todos los años): {grand_total:>15,.2f}")
    print(f"                             ({grand_total * 1000:,.0f} euros)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
