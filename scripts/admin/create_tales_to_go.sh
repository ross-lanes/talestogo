#!/bin/bash
# =============================================================================
# Create Tales To Go Distribution Package
# =============================================================================
# This script creates a clean distribution package of Tales for deployment
# at other organizations. The package includes:
# - Full application code (no user data)
# - Deployment documentation
# - Setup scripts
# - Docker configuration
#
# Usage: ./create_tales_to_go.sh [output_directory]
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DATE_STAMP=$(date +%Y%m%d)
PACKAGE_NAME="tales_to_go_${DATE_STAMP}"
OUTPUT_DIR="${1:-$PROJECT_ROOT}"

echo "============================================="
echo "  Tales To Go Package Creator"
echo "============================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Output directory: $OUTPUT_DIR"
echo "Package name: $PACKAGE_NAME"
echo ""

# Create temporary directory
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/$PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR"

echo "Creating package in: $TEMP_DIR"
echo ""

# -----------------------------------------------------------------------------
# Copy deployment kit files (documentation and setup)
# -----------------------------------------------------------------------------
echo "Copying deployment kit files..."
cp "$PROJECT_ROOT/deployment-kit/README.md" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/deployment-kit/IT_DEPLOYMENT_GUIDE.md" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/deployment-kit/IT_DEPLOYMENT_GUIDE.txt" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/deployment-kit/IT_DEPLOYMENT_GUIDE.docx" "$PACKAGE_DIR/" 2>/dev/null || echo "  (IT_DEPLOYMENT_GUIDE.docx not found, skipping)"
cp "$PROJECT_ROOT/deployment-kit/USER_GUIDE.md" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/deployment-kit/USER_GUIDE.txt" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/deployment-kit/USER_GUIDE.docx" "$PACKAGE_DIR/" 2>/dev/null || echo "  (USER_GUIDE.docx not found, skipping)"
cp "$PROJECT_ROOT/deployment-kit/.env.template" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/deployment-kit/docker-compose.yml" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/deployment-kit/setup.sh" "$PACKAGE_DIR/"
chmod +x "$PACKAGE_DIR/setup.sh"

# -----------------------------------------------------------------------------
# Copy documentation
# -----------------------------------------------------------------------------
echo "Copying documentation..."
mkdir -p "$PACKAGE_DIR/docs"
cp "$PROJECT_ROOT/docs/ENV_VARS_REFERENCE.md" "$PACKAGE_DIR/docs/" 2>/dev/null || echo "  (ENV_VARS_REFERENCE.md not found, skipping)"

# -----------------------------------------------------------------------------
# Copy application code
# -----------------------------------------------------------------------------
echo "Copying application code..."

# Backend (app/)
echo "  - Backend (app/)"
rsync -a --exclude '__pycache__' --exclude '*.pyc' --exclude '.pytest_cache' \
    "$PROJECT_ROOT/app/" "$PACKAGE_DIR/app/"

# Frontend (frontend/)
echo "  - Frontend (frontend/)"
rsync -a --exclude 'node_modules' --exclude 'dist' --exclude '.vite' \
    "$PROJECT_ROOT/frontend/" "$PACKAGE_DIR/frontend/"

# Scripts (scripts/)
echo "  - Scripts (scripts/)"
rsync -a --exclude '__pycache__' --exclude '*.pyc' \
    "$PROJECT_ROOT/scripts/" "$PACKAGE_DIR/scripts/"

# Migrations
if [ -d "$PROJECT_ROOT/migrations" ]; then
    echo "  - Migrations (migrations/)"
    rsync -a "$PROJECT_ROOT/migrations/" "$PACKAGE_DIR/migrations/"
fi

# -----------------------------------------------------------------------------
# Copy essential files
# -----------------------------------------------------------------------------
echo "Copying essential files..."
cp "$PROJECT_ROOT/Dockerfile" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/requirements.txt" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/package.json" "$PACKAGE_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/package-lock.json" "$PACKAGE_DIR/" 2>/dev/null || true

# Copy any other essential config files
cp "$PROJECT_ROOT/nixpacks.toml" "$PACKAGE_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/Procfile" "$PACKAGE_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/.dockerignore" "$PACKAGE_DIR/" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Clean up any sensitive files that may have been copied
# -----------------------------------------------------------------------------
echo "Removing any sensitive files..."
find "$PACKAGE_DIR" -name ".env" -delete
find "$PACKAGE_DIR" -name ".env.*" ! -name ".env.template" -delete
find "$PACKAGE_DIR" -name "*.db" -delete
find "$PACKAGE_DIR" -name "*.sqlite" -delete
find "$PACKAGE_DIR" -name "*.sqlite3" -delete
find "$PACKAGE_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -name ".DS_Store" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove git directories if any were copied
find "$PACKAGE_DIR" -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true

# -----------------------------------------------------------------------------
# Create the ZIP file
# -----------------------------------------------------------------------------
echo ""
echo "Creating ZIP archive..."
cd "$TEMP_DIR"
zip -r "$OUTPUT_DIR/$PACKAGE_NAME.zip" "$PACKAGE_NAME" -x "*.DS_Store" -x "*__MACOSX*"

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
echo "============================================="
echo "  Package Created Successfully!"
echo "============================================="
echo ""
echo "Output: $OUTPUT_DIR/$PACKAGE_NAME.zip"
echo ""
ZIP_SIZE=$(du -h "$OUTPUT_DIR/$PACKAGE_NAME.zip" | cut -f1)
echo "Size: $ZIP_SIZE"
echo ""
echo "Contents:"
echo "  - README.md (Quick start guide)"
echo "  - IT_DEPLOYMENT_GUIDE.md/.txt/.docx"
echo "  - USER_GUIDE.md/.txt/.docx"
echo "  - .env.template"
echo "  - docker-compose.yml"
echo "  - setup.sh"
echo "  - app/ (Backend code)"
echo "  - frontend/ (Frontend code)"
echo "  - scripts/ (Admin scripts)"
echo "  - Dockerfile"
echo "  - requirements.txt"
echo ""
echo "To test the package:"
echo "  1. Extract: unzip $PACKAGE_NAME.zip"
echo "  2. cd $PACKAGE_NAME"
echo "  3. ./setup.sh"
echo "  4. docker compose up -d"
echo "  5. docker compose exec app python scripts/admin/setup_initial_admin.py"
echo ""
