.PHONY: spendings

# Available budget years in pge/
YEARS := 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026

# Check if pge directory exists
check-pge:
	@if [ ! -d "pge" ]; then \
		echo "Error: pge directory not found. Please ensure budget data is present."; \
		exit 1; \
	fi

# Generate spendings.csv for all available years
spendings: check-pge
	@echo "Generando archivos spendings.csv para todos los años..."
	@for year in $(YEARS); do \
		if [ -d "pge/$$year" ]; then \
			echo ""; \
			echo "=== Procesando año $$year ==="; \
			sh scripts/build_spendings.sh $$year; \
		else \
			echo "  Skip año $$year (directorio no existe)"; \
		fi; \
	done
	@echo ""
	@echo "=== Proceso completado ==="
