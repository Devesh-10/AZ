#!/bin/bash
# Build Lambda deployment package locally (without Docker)
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
BACKEND_DIR="$PROJECT_DIR/backend"
BUILD_DIR="$PROJECT_DIR/lambda-build"

echo "============================================"
echo "  TIA - Test Intelligence Agent Lambda Build"
echo "============================================"
echo "Backend dir: $BACKEND_DIR"
echo "Build dir: $BUILD_DIR"

# Clean and create build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Install Python dependencies to build directory
echo ""
echo "[1/4] Installing Python dependencies for Lambda (Linux x86_64)..."
REQUIREMENTS_FILE="$BACKEND_DIR/requirements-lambda.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"
fi
pip3 install -r "$REQUIREMENTS_FILE" -t "$BUILD_DIR" --quiet --upgrade \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all:

# Copy application code
echo "[2/4] Copying application code..."
cp -r "$BACKEND_DIR/app" "$BUILD_DIR/"
cp -r "$BACKEND_DIR/data" "$BUILD_DIR/"
cp "$BACKEND_DIR/lambda_handler.py" "$BUILD_DIR/"

# Remove unnecessary files to reduce package size
echo "[3/4] Cleaning up..."
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

echo "[4/4] Build summary:"
du -sh "$BUILD_DIR"
echo ""
echo "Lambda build complete! Deploy with: cd infra && npm run deploy"
