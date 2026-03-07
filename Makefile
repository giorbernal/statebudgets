.PHONY: help spending ensemble-spending check-pge run

# Available budget years in pge/
YEARS := 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026

# Default target
.DEFAULT_GOAL := help

# Show available commands
help:
	@echo "╔════════════════════════════════════════════════════════╗"
	@echo "║   Presupuestos Generales del Estado - Comandos        ║"
	@echo "╚════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  make help              - Muestra esta ayuda"
	@echo ""
	@echo "  make run               - Ejecuta la aplicación Streamlit"
	@echo "                           (Acceso: http://localhost:8501)"
	@echo ""
	@echo "  make spending          - Genera spending.csv para todos los años"
	@echo "                           (2011-2026)"
	@echo ""
	@echo "  make ensemble-spending - Ensambla todos los spending.csv en un"
	@echo "                           archivo global (data/input/spending.csv)"
	@echo ""

# Check if pge directory exists
check-pge:
	@if [ ! -d "pge" ]; then \
		echo "Error: pge directory not found. Please ensure budget data is present."; \
		exit 1; \
	fi

# Generate spending.csv for all available years
spending: check-pge
	@echo "Generando archivos spending.csv para todos los años..."
	@for year in $(YEARS); do \
		if [ -d "pge/$$year" ]; then \
			echo ""; \
			echo "=== Procesando año $$year ==="; \
			python3.10 scripts/build_spending.py $$year; \
		else \
			echo "  Skip año $$year (directorio no existe)"; \
		fi; \
	done
	@echo ""
	@echo "=== Proceso completado ==="

# Ensemble all spending.csv into a single global file
ensemble-spending: check-pge
	@echo "Ensembling all spending.csv files..."
	@sh scripts/ensemble_spending.sh

# Run the Streamlit application
run:
	@echo "Iniciando aplicación Streamlit..."
	@echo "Acceso: http://localhost:8501"
	@echo ""
	cd app && streamlit run Gasto_anual.py
