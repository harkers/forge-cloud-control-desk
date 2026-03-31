# Makefile for Forge Compute Control Desk

.PHONY: help install test roundtrip create delete start stop validate

VM ?= forge-test-vm
REASON ?= Makefile invocation

help:
	@echo "Forge Compute Control Desk"
	@echo ""
	@echo "Available targets:"
	@echo "  install   - Install Python dependencies"
	@echo "  test      - Run a single workflow action (VM=name ACTION=start)"
	@echo "  roundtrip - Create, inspect, delete a disposable test VM (cost-safe)"
	@echo "  create    - Create a VM"
	@echo "  delete    - Delete a VM"
	@echo "  start     - Start a VM"
	@echo "  stop      - Stop a VM"
	@echo "  validate  - Validate environment setup"
	@echo "  help      - Show this help"

install:
	pip install -r requirements.txt

test:
	python tests/test_start_instance.py $(ACTION) $(VM) "$(REASON)"

roundtrip:
	python tests/test_start_instance.py roundtrip $(VM) "Roundtrip test"

create:
	python tests/test_start_instance.py create $(VM) "$(REASON)"

delete:
	python tests/test_start_instance.py delete $(VM) "$(REASON)"

start:
	python tests/test_start_instance.py start $(VM) "$(REASON)"

stop:
	python tests/test_start_instance.py stop $(VM) "$(REASON)"

validate:
	@echo "Validating environment..."
	@test -f .env || (echo ".env file not found"; exit 1)
	@echo ".env file found"
	@test -n "$(GCP_SERVICE_ACCOUNT_JSON)" && test -f "$(GCP_SERVICE_ACCOUNT_JSON)" || echo "Warning: GCP_SERVICE_ACCOUNT_JSON not set or file missing"
	@echo "Validation complete"
