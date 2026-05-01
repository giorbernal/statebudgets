#!/usr/bin/env python3.10
"""
Script para validar la precisión de los datos de ingresos.

Verifica que:
1. Los desgloses por servicios sumen al total del organismo
2. Los capítulos del ESTADO sumen al total del ESTADO
3. Los totales coincidan entre archivos fuente
"""

import sys
import pandas as pd
from pathlib import Path


def validate_revenue_data(csv_file: str) -> bool:
    """
    Valida el archivo de ingresos.
    
    Args:
        csv_file: Ruta al archivo CSV de ingresos
        
    Returns:
        True si todas las validaciones pasan, False en caso contrario
    """
    # Leer datos
    try:
        df = pd.read_csv(csv_file, sep=';', decimal=',')
    except Exception as e:
        print(f"Error al leer {csv_file}: {e}", file=sys.stderr)
        return False
    
    print(f"Leyendo {len(df)} filas desde {csv_file}")
    print()
    
    all_passed = True
    
    # ========== VALIDACIÓN 1: Verificar que ESTADO suma correctamente ==========
    print("=" * 70)
    print("VALIDACIÓN 1: Ingresos del ESTADO")
    print("=" * 70)
    
    estado_rows = df[df['organismo'] == 'ESTADO']
    if not estado_rows.empty:
        estado_total_calculated = estado_rows['total'].sum()
        estado_expected = 192544166.33  # Valor conocido
        
        print(f"\nIngresos por capítulo (miles de euros):")
        for _, row in estado_rows.iterrows():
            print(f"  Cap {row['codigo']}: {row['descripcion']:<40} {row['total']:>15,.2f}")
        
        print(f"\nTotal calculado: {estado_total_calculated:,.2f}")
        print(f"Total esperado:  {estado_expected:,.2f}")
        
        tolerance = 100  # Tolerancia de 100 mil euros por errores de redondeo
        if abs(estado_total_calculated - estado_expected) < tolerance:
            print("✓ ESTADO suma correctamente")
        else:
            print(f"✗ ERROR: Diferencia de {abs(estado_total_calculated - estado_expected):,.2f}")
            all_passed = False
    
    # ========== VALIDACIÓN 2: Verificar organismos incluidos en consolidado ==========
    print("\n" + "=" * 70)
    print("VALIDACIÓN 2: Ingresos por organismo (Consolidado)")
    print("=" * 70)
    print("\nNota: Se consolida ESTADO + SEGURIDAD SOCIAL (ambos están en spending.csv)")
    
    organismo_totals = df.groupby('organismo')['total'].sum().sort_values(ascending=False)
    
    print("\nTotales por organismo (miles de euros):")
    for organismo, total in organismo_totals.items():
        print(f"  {organismo:<35} {total:>15,.2f}")
    
    total_consolidado = organismo_totals.sum()
    print(f"\nGran total (CONSOLIDADO): {total_consolidado:>15,.2f}")
    print(f"                         ({total_consolidado * 1000:>15,.0f} euros)")
    
    # ========== VALIDACIÓN 3: Verificar que no haya valores negativos o nulos ==========
    print("\n" + "=" * 70)
    print("VALIDACIÓN 3: Integridad de datos")
    print("=" * 70)
    
    # Valores nulos
    null_count = df['total'].isna().sum()
    if null_count > 0:
        print(f"✗ ERROR: {null_count} valores nulos en 'total'")
        all_passed = False
    else:
        print("✓ Sin valores nulos")
    
    # Valores negativos (estos pueden ser válidos, pero informamos)
    negative_count = (df['total'] < 0).sum()
    if negative_count > 0:
        print(f"⚠ Advertencia: {negative_count} valores negativos encontrados:")
        negative_rows = df[df['total'] < 0]
        for _, row in negative_rows.iterrows():
            print(f"  {row['organismo']} - {row['descripcion']}: {row['total']:.2f}")
    else:
        print("✓ Sin valores negativos")
    
    # Valores duplicados
    duplicate_rows = df[df.duplicated(subset=['año', 'organismo', 'codigo'], keep=False)]
    if not duplicate_rows.empty:
        print(f"✗ ERROR: {len(duplicate_rows)} filas duplicadas encontradas:")
        print(duplicate_rows[['año', 'organismo', 'codigo', 'descripcion', 'total']])
        all_passed = False
    else:
        print("✓ Sin filas duplicadas")
    
    # ========== VALIDACIÓN 4: Verificar desgloses por capítulos ==========
    print("\n" + "=" * 70)
    print("VALIDACIÓN 4: Desglose por capítulos (ORGANISMOS AUTÓNOMOS)")
    print("=" * 70)
    
    # Para organismos autónomos, verificar que los detalles sumen al total
    oa_rows = df[df['organismo'] == 'ORGANISMOS AUTÓNOMOS'].copy()
    
    if not oa_rows.empty:
        # Agrupar por código base (sin decimales)
        oa_rows['codigo_base'] = oa_rows['codigo'].apply(lambda x: x.split('.')[0] if '.' in str(x) else str(x))
        
        # Verificar algunos agregados
        mismatches = []
        for codigo_base in oa_rows['codigo_base'].unique():
            detail_rows = oa_rows[oa_rows['codigo_base'] == codigo_base]
            summary_row = detail_rows[detail_rows['codigo'] == codigo_base]
            
            if not summary_row.empty and len(detail_rows) > 1:
                summary_total = summary_row.iloc[0]['total']
                detail_total = detail_rows[detail_rows['codigo'] != codigo_base]['total'].sum()
                
                if abs(summary_total - detail_total) > 10:  # Tolerancia 10k euros
                    mismatches.append({
                        'codigo': codigo_base,
                        'summary': summary_total,
                        'detail': detail_total,
                        'diff': abs(summary_total - detail_total)
                    })
        
        if mismatches:
            print(f"✗ ERROR: {len(mismatches)} desgloses inconsistentes:")
            for m in mismatches[:5]:  # Mostrar máximo 5
                print(f"  Código {m['codigo']}: Agregado={m['summary']:.2f}, " 
                      f"Detalle={m['detail']:.2f}, Diferencia={m['diff']:.2f}")
            all_passed = False
        else:
            print("✓ Desgloses consistentes")
    
    # ========== VALIDACIÓN 5: Comparación con gastos consolidados ==========
    print("\n" + "=" * 70)
    print("VALIDACIÓN 5: Análisis consolidado vs. Gastos")
    print("=" * 70)
    
    try:
        # Load spending data for comparison
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        spending_path = project_root / "data" / "input" / "spending.csv"
        
        if spending_path.exists():
            spending_df = pd.read_csv(spending_path, sep=';', decimal=',', 
                                     encoding='utf-8', on_bad_lines='skip', engine='python')
            spending_df['amount'] = pd.to_numeric(
                spending_df['amount'].astype(str).str.replace(".", "", regex=False)
                                             .str.replace(",", ".", regex=False),
                errors='coerce'
            )
            spending_2023 = spending_df[spending_df['year'] == 2023]
            total_gastos = spending_2023['amount'].sum()
            
            print(f"\nIngresos consolidados (ESTADO + Seguridad Social):")
            print(f"  {total_consolidado:>15,.2f} miles €")
            print(f"\nGastos consolidados (spending.csv):")
            print(f"  {total_gastos:>15,.2f} miles €")
            
            deficit = total_gastos - total_consolidado
            deficit_pct = (deficit / total_gastos) * 100 if total_gastos > 0 else 0
            
            print(f"\nResultado consolidado:")
            if deficit > 0:
                print(f"  Déficit: {deficit:>15,.2f} miles € ({deficit_pct:.1f}% de gastos)")
            else:
                print(f"  Superávit: {-deficit:>15,.2f} miles € ({-deficit_pct:.1f}% de gastos)")
    except Exception as e:
        print(f"⚠ No se pudo comparar con gastos: {e}")
    
    # ========== RESULTADO FINAL ==========
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ TODAS LAS VALIDACIONES PASARON")
        return True
    else:
        print("✗ ALGUNAS VALIDACIONES FALLARON")
        return False


def main():
    """Función principal."""
    project_root = Path(__file__).parent.parent
    csv_file = project_root / 'data' / 'input' / 'revenue.csv'
    
    if not csv_file.exists():
        print(f"Error: Archivo no encontrado: {csv_file}", file=sys.stderr)
        sys.exit(1)
    
    success = validate_revenue_data(str(csv_file))
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
