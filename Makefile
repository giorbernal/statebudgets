.PHONY: spending ensemble-spending

# Available budget years in pge/
YEARS := 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026

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
			sh scripts/build_spending.sh $$year; \
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
