#!/usr/bin/env python3.10
"""
Módulo con parsers independientes para diferentes formatos de ingresos presupuestarios.

Soporta múltiples formatos históricos del PGE:
- HTML (2011-2016): Tablas HTML convertidas del original
- CSV clásico (2017-2023): Formato N_XX_E_R_2_[organismo]_1_7_A_1.CSV
- CSV nuevo (2024-2026): Formato N_*P_E_V_1_* con nueva estructura
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from html.parser import HTMLParser
import pandas as pd


def normalize_amount(amount_str: str) -> float:
    """
    Normaliza cantidad en formato español (1.234,56) a float.
    
    Args:
        amount_str: Cadena con formato español
        
    Returns:
        Float con el valor en miles de euros
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


# ============================================================================
# PARSER HTML (2011-2016)
# ============================================================================

class RevenueTableHTMLParser(HTMLParser):
    """Parser HTML para extraer tablas de ingresos presupuestarios."""
    
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_row = []
        self.rows = []
        self.current_text = ""
    
    def handle_starttag(self, tag, attrs):
        """Procesa etiquetas de apertura."""
        if tag == 'table':
            self.in_table = True
        elif tag == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag in ('td', 'th') and self.in_row:
            self.in_cell = True
            self.current_text = ""
    
    def handle_endtag(self, tag):
        """Procesa etiquetas de cierre."""
        if tag == 'table' and self.in_table:
            self.in_table = False
        elif tag == 'tr' and self.in_row:
            self.in_row = False
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag in ('td', 'th') and self.in_cell:
            self.in_cell = False
            # Limpiar entidades HTML
            cell_text = self.current_text.strip()
            cell_text = cell_text.replace('&#49;', '1').replace('&#50;', '2')
            cell_text = cell_text.replace('&#51;', '3').replace('&#52;', '4')
            cell_text = cell_text.replace('&#53;', '5').replace('&#54;', '6')
            cell_text = cell_text.replace('&#55;', '7').replace('&#56;', '8')
            cell_text = cell_text.replace('&#57;', '9').replace('&#48;', '0')
            cell_text = cell_text.replace('&#46;', '.').replace('&#44;', ',')
            cell_text = cell_text.replace('&#40;', '(').replace('&#41;', ')')
            cell_text = cell_text.replace('&#233;', 'é').replace('&#243;', 'ó')
            self.current_row.append(cell_text)
    
    def handle_data(self, data):
        """Procesa datos de texto."""
        if self.in_cell:
            self.current_text += data


def parse_html_revenue(file_path: Path, organismo: str, year: int) -> List[Dict]:
    """
    Parsea archivo HTML de ingresos presupuestarios (2011-2016).
    
    Args:
        file_path: Ruta al archivo HTM
        organismo: 'ESTADO' o 'SEGURIDAD SOCIAL'
        year: Año del presupuesto
        
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
    
    # Parser HTML
    parser = RevenueTableHTMLParser()
    try:
        parser.feed(content)
    except Exception as e:
        print(f"Error parseando HTML {file_path}: {e}", file=sys.stderr)
        return []
    
    # Procesar filas extraídas
    # Formato esperado: [Económica, Explicación, Total]
    for row_idx, row in enumerate(parser.rows):
        if len(row) < 3:
            continue
        
        # Saltar encabezados
        if row_idx == 0 and ('Económica' in row[0] or 'Explicación' in row[0]):
            continue
        
        codigo = row[0].strip() if len(row) > 0 else ''
        descripcion = row[1].strip() if len(row) > 1 else ''
        total_str = row[2].strip() if len(row) > 2 else ''
        
        # Solo aceptar códigos de un dígito (1-8)
        if codigo and codigo.isdigit() and 1 <= int(codigo) <= 8:
            amount = normalize_amount(total_str)
            rows.append({
                'año': year,
                'organismo': organismo,
                'codigo': codigo,
                'descripcion': descripcion,
                'total': amount,
                'cap1': 0.0, 'cap2': 0.0, 'cap3': 0.0, 'cap4': 0.0,
                'cap5': 0.0, 'cap6': 0.0, 'cap7': 0.0, 'cap8': 0.0,
            })
    
    return rows


# ============================================================================
# PARSER CSV NUEVO (2024-2026)
# ============================================================================

def parse_csv_revenue_new_format(file_path: Path, organismo: str, year: int) -> List[Dict]:
    """
    Parsea archivos CSV del nuevo formato PGE (2024-2026).
    
    Formato: N_*P_E_R_31_[organismo]_* con capítulos económicos (1-8).
    Estructura: código;descripción;valores_intermedios...;total
    
    Args:
        file_path: Ruta al archivo CSV
        organismo: 'ESTADO' o 'SEGURIDAD SOCIAL'
        year: Año del presupuesto
        
    Returns:
        Lista de diccionarios con datos de ingresos por capítulo
    """
    rows = []
    chapters_data = {}  # Agregar totales por capítulo
    
    try:
        with open(file_path, 'r', encoding='windows-1252', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"Error al leer {file_path}: {e}", file=sys.stderr)
        return []
    
    lines = content.split('\n')
    
    # Procesar todas las líneas buscando capítulos (1-8)
    for line in lines:
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        
        parts = [p.strip() for p in line.split(';')]
        
        if len(parts) < 2:
            continue
        
        codigo = parts[0]
        
        # Verificar si es un capítulo (1-8)
        if codigo and codigo.isdigit() and 1 <= int(codigo) <= 8:
            descripcion = parts[1] if len(parts) > 1 else ''
            
            # El total suele estar en el penúltimo o último valor numérico
            total_str = '0'
            if len(parts) > 2:
                # Buscar el último valor que coincida con formato numérico
                for j in range(len(parts) - 1, 0, -1):
                    if parts[j] and re.match(r'^[-+]?[\d.]+,\d+$|^[-+]?\d+$', parts[j]):
                        total_str = parts[j]
                        break
            
            amount = normalize_amount(total_str)
            
            if amount > 0:  # Solo guardar si hay cantidad
                # Agregar o actualizar el capítulo
                if codigo not in chapters_data:
                    chapters_data[codigo] = {
                        'codigo': codigo,
                        'descripcion': descripcion if descripcion else f'CAPÍTULO {codigo}',
                        'total': amount,
                    }
                else:
                    # Si ya existe, acumular (en caso de múltiples líneas)
                    chapters_data[codigo]['total'] += amount
    
    # Convertir diccionario a lista de filas ordenadas
    for codigo in sorted(chapters_data.keys(), key=lambda x: int(x)):
        data = chapters_data[codigo]
        rows.append({
            'año': year,
            'organismo': organismo,
            'codigo': data['codigo'],
            'descripcion': data['descripcion'],
            'total': data['total'],
            'cap1': 0.0, 'cap2': 0.0, 'cap3': 0.0, 'cap4': 0.0,
            'cap5': 0.0, 'cap6': 0.0, 'cap7': 0.0, 'cap8': 0.0,
        })
    
    return rows


def find_revenue_files_html(pge_year_path: Path, year: int) -> Dict[str, Path]:
    """
    Busca archivos HTML de ingresos para años 2011-2016.
    
    Args:
        pge_year_path: Ruta a carpeta del año (pge/YYYY/PGE-ROM)
        year: Año del presupuesto
        
    Returns:
        Dict con rutas a archivos por organismo
    """
    files = {
        'estado': None,
        'seguridad_social': None,
    }
    
    htm_path = pge_year_path / 'doc' / 'HTM'
    if htm_path.exists():
        # Buscar N_XX_E_R_2_101_1_7_A_1.HTM (ESTADO)
        for f in htm_path.glob('*_E_R_2_101_1_7_A_1.HTM'):
            files['estado'] = f
            break
        
        # Buscar N_XX_E_R_2_105_1_7_A_1.HTM (SEGURIDAD SOCIAL)
        for f in htm_path.glob('*_E_R_2_105_1_7_A_1.HTM'):
            files['seguridad_social'] = f
            break
    
    return files


def find_revenue_files_new_format(pge_year_path: Path, year: int) -> Dict[str, Path]:
    """
    Busca archivos CSV del nuevo formato (2024-2026).
    
    Busca archivos R_31 que contienen capítulos económicos consolidados.
    
    Args:
        pge_year_path: Ruta a carpeta del año (pge/YYYY/PGE-ROM)
        year: Año del presupuesto
        
    Returns:
        Dict con rutas a archivos por organismo
    """
    files = {
        'estado': None,
        'seguridad_social': None,
    }
    
    csv_path = pge_year_path / 'doc' / 'CSV'
    if csv_path.exists():
        # Buscar patrón R_31_101_* (ESTADO - consolidado con capítulos)
        candidates = list(csv_path.glob('*_E_R_31_101_1_*_1_1.CSV'))
        if candidates:
            files['estado'] = candidates[0]  # Tomar el primero
        
        # Buscar patrón R_31_105_* (SEGURIDAD SOCIAL - consolidado)
        candidates = list(csv_path.glob('*_E_R_31_105_1_*_1_1.CSV'))
        if candidates:
            files['seguridad_social'] = candidates[0]
    
    return files


# ============================================================================
# INTEGRADORES POR AÑO
# ============================================================================

def build_revenue_html_format(pge_root: str, year: int) -> pd.DataFrame:
    """
    Construye dataset de ingresos desde archivos HTML (2011-2016).
    
    Args:
        pge_root: Ruta raíz de carpeta PGE
        year: Año del presupuesto
        
    Returns:
        DataFrame con ingresos consolidados
    """
    pge_year_path = Path(pge_root) / str(year) / 'PGE-ROM'
    
    if not pge_year_path.exists():
        print(f"⚠ Año {year}: Directorio no encontrado", file=sys.stderr)
        return pd.DataFrame()
    
    all_data = []
    files = find_revenue_files_html(pge_year_path, year)
    
    # ESTADO
    if files['estado']:
        print(f"  Procesando {files['estado'].name} (ESTADO - HTML)...")
        data = parse_html_revenue(files['estado'], 'ESTADO', year)
        print(f"    ✓ {len(data)} capítulos extraídos")
        all_data.extend(data)
    else:
        print(f"  ⚠ Año {year}: No se encontró archivo de ESTADO (HTML)")
    
    # SEGURIDAD SOCIAL
    if files['seguridad_social']:
        print(f"  Procesando {files['seguridad_social'].name} (SS - HTML)...")
        data = parse_html_revenue(files['seguridad_social'], 'SEGURIDAD SOCIAL', year)
        print(f"    ✓ {len(data)} capítulos extraídos")
        all_data.extend(data)
    else:
        print(f"  ⚠ Año {year}: No se encontró archivo de SS (HTML)")
    
    if not all_data:
        print(f"✗ Año {year}: No se extrajeron datos", file=sys.stderr)
        return pd.DataFrame()
    
    df = pd.DataFrame(all_data)
    cols = ['año', 'organismo', 'codigo', 'descripcion', 'total']
    cap_cols = [col for col in df.columns if col.startswith('cap')]
    if cap_cols:
        cols.extend(sorted(cap_cols))
    
    df = df[[col for col in cols if col in df.columns]]
    
    return df


def build_revenue_new_format(pge_root: str, year: int) -> pd.DataFrame:
    """
    Construye dataset de ingresos del nuevo formato PGE (2024-2026).
    
    Args:
        pge_root: Ruta raíz de carpeta PGE
        year: Año del presupuesto
        
    Returns:
        DataFrame con ingresos consolidados
    """
    pge_year_path = Path(pge_root) / str(year) / 'PGE-ROM'
    
    if not pge_year_path.exists():
        print(f"⚠ Año {year}: Directorio no encontrado", file=sys.stderr)
        return pd.DataFrame()
    
    all_data = []
    files = find_revenue_files_new_format(pge_year_path, year)
    
    # ESTADO
    if files['estado']:
        print(f"  Procesando {files['estado'].name} (ESTADO - nuevo formato)...")
        data = parse_csv_revenue_new_format(files['estado'], 'ESTADO', year)
        print(f"    ✓ {len(data)} capítulos extraídos")
        all_data.extend(data)
    else:
        print(f"  ⚠ Año {year}: No se encontró archivo de ESTADO (nuevo formato)")
    
    # SEGURIDAD SOCIAL
    if files['seguridad_social']:
        print(f"  Procesando {files['seguridad_social'].name} (SS - nuevo formato)...")
        data = parse_csv_revenue_new_format(files['seguridad_social'], 'SEGURIDAD SOCIAL', year)
        print(f"    ✓ {len(data)} capítulos extraídos")
        all_data.extend(data)
    else:
        print(f"  ⚠ Año {year}: No se encontró archivo de SS (nuevo formato)")
    
    if not all_data:
        print(f"✗ Año {year}: No se extrajeron datos", file=sys.stderr)
        return pd.DataFrame()
    
    df = pd.DataFrame(all_data)
    cols = ['año', 'organismo', 'codigo', 'descripcion', 'total']
    cap_cols = [col for col in df.columns if col.startswith('cap')]
    if cap_cols:
        cols.extend(sorted(cap_cols))
    
    df = df[[col for col in cols if col in df.columns]]
    
    return df
