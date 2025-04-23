# List of all apps (detected automatically)
APPS := $(shell find apps -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)
PY := python3

.PHONY: help list all clean $(APPS)

help:
	@echo "Usage:"
	@echo "  make list             - List all available apps"
	@echo "  make all              - Install all apps"
	@echo "  make app1 app2 ...    - Install specific apps"
	@echo "  make clean            - Clean __pycache__ folders"

list:
	@echo "Available apps:"
	@$(foreach app,$(APPS),echo "  - $(app)";)

all: $(APPS)

$(APPS):
	@echo "🔧 Installing $@..."

	# Install Ubuntu packages
	@if [ -f apps/$@/packages.apt ]; then \
		echo "Installing Ubuntu packages for $@"; \
		sudo apt-get update && sudo xargs -a apps/$@/packages.apt apt-get install -y; \
	fi

	# Install Python requirements
	@if [ -f apps/$@/requirements.txt ]; then \
		echo "Installing Python packages for $@"; \
		$(PY) -m pip install -r apps/$@/requirements.txt; \
	fi

	@echo "✅ $@ installed successfully!"

clean:
	find . -type d -name '__pycache__' -exec rm -r {} +
