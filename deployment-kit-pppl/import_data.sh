#!/bin/bash
# =============================================================================
# PPPL Brand Data Import Script
# =============================================================================
# This script imports PPPL brand data after initial Tales setup.
#
# Prerequisites:
# 1. Tales containers must be running (docker compose up -d)
# 2. Initial admin account must be created
# 3. Data files must exist in ./data/ directory
# =============================================================================

set -e

echo "============================================="
echo "  PPPL Brand Data Import"
echo "============================================="
echo ""

# Check if containers are running
if ! docker compose ps | grep -q "Up"; then
    echo "ERROR: Tales containers are not running."
    echo "Please start them first: docker compose up -d"
    exit 1
fi

# Get admin email from environment or use default
ADMIN_EMAIL="${ADMIN_EMAIL:-rkremen@pppl.gov}"
echo "Admin email: $ADMIN_EMAIL"
echo ""

# Check for PPPL brand data
if [ -f "./data/pppl_brand.json" ]; then
    echo "Importing PPPL brand data..."
    docker compose exec -T app python scripts/admin/import_brand_data.py \
        --file /app/data/pppl_brand.json \
        --admin-email "$ADMIN_EMAIL"
    echo "PPPL brand imported successfully!"
    echo ""
else
    echo "WARNING: ./data/pppl_brand.json not found, skipping PPPL import."
    echo ""
fi

# Check for Princeton Engineering brand data
if [ -f "./data/princeton_engineering_brand.json" ]; then
    echo "Importing Princeton Engineering brand data..."
    docker compose exec -T app python scripts/admin/import_brand_data.py \
        --file /app/data/princeton_engineering_brand.json \
        --admin-email "$ADMIN_EMAIL"
    echo "Princeton Engineering brand imported successfully!"
    echo ""
else
    echo "INFO: ./data/princeton_engineering_brand.json not found, skipping."
    echo ""
fi

echo "============================================="
echo "  Import Complete!"
echo "============================================="
echo ""
echo "Next steps:"
echo "1. Open Tales in your browser: http://localhost:8080"
echo "2. Log in with your admin account"
echo "3. Verify the imported brands appear in the UI"
echo ""
echo "To import additional brands later:"
echo "  docker compose exec app python scripts/admin/import_brand_data.py \\"
echo "    --file /app/data/your_brand.json --admin-email $ADMIN_EMAIL"
echo ""
