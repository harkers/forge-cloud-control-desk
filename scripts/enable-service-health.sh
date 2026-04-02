#!/bin/bash
# Enable Service Health API for GCCD-001
# Run this on a machine with gcloud CLI installed

set -e

PROJECT_ID="301823798218"
PROJECT_NAME="orderededge-groupware"

echo "🔧 Enabling Cloud Resource Manager API for GCCD-001"
echo "   Project: $PROJECT_NAME ($PROJECT_ID)"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found!"
    echo ""
    echo "Install it first:"
    echo "  - Debian/Ubuntu: sudo apt install google-cloud-sdk"
    echo "  - macOS: brew install --cask google-cloud-sdk"
    echo "  - Or: https://cloud.google.com/sdk/docs/install"
    echo ""
    echo "Then authenticate:"
    echo "  gcloud auth login"
    echo "  gcloud config set project $PROJECT_ID"
    exit 1
fi

# Check authentication
echo "📋 Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ No active gcloud account found!"
    echo ""
    echo "Run: gcloud auth login"
    exit 1
fi

# Set project
echo "📋 Setting project to $PROJECT_NAME..."
gcloud config set project $PROJECT_ID

# Enable the API
echo "🚀 Enabling Cloud Resource Manager API..."
gcloud services enable cloudresourcemanager.googleapis.com

echo ""
echo "✅ API enabled successfully!"
echo ""
echo "📝 Next steps:"
echo "  1. Wait ~30 seconds for propagation"
echo "  2. Test: cd projects/forge-cloud-control-desk && python3 -m main health"
echo "  3. Check evidence: cat data/evidence/service_health/health_check_*.md"
echo ""
