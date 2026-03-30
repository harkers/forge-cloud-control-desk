# Makefile for Forge Compute Control Desk

.PHONY: help install test start validate

help:
	@echo "Forge Compute Control Desk"
	@echo ""
	@echo "Available targets:"
	@echo "  install  - Install Python dependencies"
	@echo "  test     - Run tests"
	@echo "  start    - Test start instance workflow"
	@echo "  validate - Validate environment setup"
	@echo "  help     - Show this help"

install:
	pip install -r requirements.txt

test:
	python tests/test_start_instance.py $(VM)

start:
	@echo "Starting instance: $(VM)"
	python src/core/start_instance.py $(VM) $(REASON)

validate:
	@echo "Validating environment..."
	@test -f .env || (echo "❌ .env file not found"; exit 1)
	@echo "✅ .env file found"
	@test -f $(GCP_SERVICE_ACCOUNT_JSON) || (echo "❌ Service account JSON not found at $(GCP_SERVICE_ACCOUNT_JSON)"; exit 1)
	@echo "✅ Service account JSON found"
	@test -f $(GMAIL_CLIENT_SECRETS) || (echo "❌ Gmail client secrets not found at $(GMAIL_CLIENT_SECRETS)"; exit 1)
	@echo "✅ Gmail client secrets found"
	@echo "✅ All checks passed"
