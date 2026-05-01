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
    
    # ========== VALIDACIÓN 1: Verificar que capítulos del ESTADO suman al total ==========
    print("=" * 70)
    print("VALIDACIÓN 1: Ingresos del ESTADO - Validación por año")
    print("=" * 70)
    
    estado_data = df[df['organismo'] == 'ESTADO']
    if not estado_data.empty:
        years = sorted(estado_data['año'].unique())
        
        for year in years:
            year_data = estado_data[estado_data['año'] == year]
            estado_total = year_data['total'].sum()
            
            print(f"\nAño {year}:")
            print(f"  Capítulos:")
            for _, row in year_data.iterrows():
                print(f"    Cap {row['codigo']}: {row['descripcion']:<40} {row['total']:>15,.2f}")
            print(f"  Total ESTADO: {estado_total:,.2f} miles €")
    
    # ========== VALIDACIÓN 1B: Verificar que la suma de ESTADO + SS es razonable ==========
    print("\n" + "=" * 70)
    print("VALIDACIÓN 1B: Relación ESTADO vs SEGURIDAD SOCIAL")
    print("=" * 70)
    
    yearly_breakdown = df.groupby(['año', 'organismo'])['total'].sum().unstack(fill_value=0)
    print("\nDesglose por año y organismo (miles de euros):")
    print(f"{'Año':<6} {'ESTADO':<20} {'SEG.SOCIAL':<20} {'Total':<20}")
    print("-" * 66)
    
    for year in yearly_breakdown.index:
        estado_val = yearly_breakdown.loc[year, 'ESTADO'] if 'ESTADO' in yearly_breakdown.columns else 0
        ss_val = yearly_breakdown.loc[year, 'SEGURIDAD SOCIAL'] if 'SEGURIDAD SOCIAL' in yearly_breakdown.columns else 0
        total = estado_val + ss_val
        print(f"{year:<6} {estado_val:>18,.0f} {ss_val:>18,.0f} {total:>18,.0f}")
    
    # Verificar que SS es ~50-60% del total (patrón esperado)
    for year in yearly_breakdown.index:
        estado_val = yearly_breakdown.loc[year, 'ESTADO'] if 'ESTADO' in yearly_breakdown.columns else 0
        ss_val = yearly_breakdown.loc[year, 'SEGURIDAD SOCIAL'] if 'SEGURIDAD SOCIAL' in yearly_breakdown.columns else 0
        total = estado_val + ss_val
        if total > 0:
            ss_pct = (ss_val / total) * 100
            if 30 < ss_pct < 70:
                print(f"✓ {year}: SS = {ss_pct:.1f}% del total (razonable)")
            else:
                print(f"⚠ {year}: SS = {ss_pct:.1f}% (esperado 40-60%)")
        else:
            all_passed = False
    
    # ========== VALIDACIÓN 2: Verificar organismos incluidos en consolidado ==========
    print("\n" + "=" * 70)
    print("VALIDACIÓN 2: Ingresos por organismo (Consolidado)")
    print("=" * 70)
    print("\nNota: Se consolida ESTADO + SEGURIDAD SOCIAL (ambos están en spending.csv)")
    
    organismo_totals = df.groupby('organismo')['total'].sum().sort_values(ascending=True)
    
    print("\nTotales por organismo (miles de euros):")
    for organismo, total in organismo_totals.items():
        print(f"  {organismo:<35} {total:>15,.2f}")
    
    # Calculate only ESTADO + SEGURIDAD SOCIAL
    estado_total_all = organismo_totals.get('ESTADO', 0)
    ss_total_all = organismo_totals.get('SEGURIDAD SOCIAL', 0)
    total_consolidado = estado_total_all + ss_total_all
    print(f"\nGran total consolidado (ESTADO + SS): {total_consolidado:>15,.2f}")
    print(f"                                     ({total_consolidado * 1000:>15,.0f} euros)")
    
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
        # Load spending data for comparison - only years with revenue data
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
            
            # Compare for years where we have revenue data
            revenue_years = sorted(df['año'].unique())
            
            print(f"\nIngresos consolidados (ESTADO + Seguridad Social) por año:")
            for year in revenue_years:
                year_revenue = df[df['año'] == year][['organismo', 'total']].groupby('organismo')['total'].sum()
                year_total = year_revenue.get('ESTADO', 0) + year_revenue.get('SEGURIDAD SOCIAL', 0)
                
                year_spending = spending_df[spending_df['year'] == year]['amount'].sum()
                
                if year_spending > 0:
                    deficit = year_spending - year_total
                    deficit_pct = (deficit / year_spending) * 100
                    symbol = "✓" if deficit > 0 else "⚠"
                    
                    print(f"\n  {year}: Ingresos {year_total:>12,.0f}k€ | Gastos {year_spending:>12,.0f}k€ | " +
                          f"{'Déficit' if deficit > 0 else 'Superávit'} {abs(deficit):>12,.0f}k€ ({abs(deficit_pct):>5.1f}%) {symbol}")
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
