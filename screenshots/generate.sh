#!/bin/bash
# Generate and validate screenshots for documentation
#
# Usage: ./screenshots/generate.sh [tape_name]
#   If tape_name is provided, only generate that screenshot
#   Otherwise, generate all screenshots

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
IMAGES_DIR="$PROJECT_DIR/docs/images"
FONT_PATH="$SCRIPT_DIR/fonts/JetBrainsMonoNL-Regular.ttf"

# Minimum file size in bytes (screenshots should be at least 1KB)
MIN_SIZE=1000

# Error patterns to check for in screenshots (requires tesseract for OCR)
ERROR_PATTERNS="command not found|No such file|Error|Traceback"

run_vhs() {
    local tape="$1"
    local name="$(basename "$tape" .tape)"

    echo "Generating $name..."

    docker run --rm -t \
        -v "$PROJECT_DIR:/app" \
        -v "$FONT_PATH:/usr/share/fonts/JetBrainsMonoNL-Regular.ttf" \
        -w /app/docs/images \
        ghcr.io/charmbracelet/vhs "/app/screenshots/${name}.tape" 2>&1 | \
        grep -E "(Error|error|failed)" && return 1 || true

    return 0
}

validate_screenshot() {
    local name="$1"
    local png="$IMAGES_DIR/${name}.png"

    # Check file exists
    if [[ ! -f "$png" ]]; then
        echo "  FAIL: $png not found"
        return 1
    fi

    # Check minimum size
    local size=$(stat -f%z "$png" 2>/dev/null || stat -c%s "$png" 2>/dev/null)
    if [[ $size -lt $MIN_SIZE ]]; then
        echo "  FAIL: $png too small ($size bytes, minimum $MIN_SIZE)"
        return 1
    fi

    # Optional: OCR check for error messages (if tesseract is available)
    if command -v tesseract &> /dev/null; then
        local text=$(tesseract "$png" - 2>/dev/null || true)
        if echo "$text" | grep -qiE "$ERROR_PATTERNS"; then
            echo "  FAIL: $png contains error text"
            echo "  Text found: $(echo "$text" | grep -iE "$ERROR_PATTERNS" | head -1)"
            return 1
        fi
    fi

    echo "  OK: $png ($size bytes)"
    return 0
}

cleanup() {
    # Remove temp gif files
    rm -f "$IMAGES_DIR"/*_temp.gif 2>/dev/null || true
}

# Main
TAPES=(menu worklist form table selection tabular message)

if [[ -n "$1" ]]; then
    TAPES=("$1")
fi

echo "=== Generating Screenshots ==="
echo ""

FAILED=0
for tape in "${TAPES[@]}"; do
    if ! run_vhs "$tape"; then
        echo "  FAIL: VHS failed for $tape"
        ((FAILED++))
        continue
    fi

    if ! validate_screenshot "$tape"; then
        ((FAILED++))
    fi
done

cleanup

echo ""
echo "=== Summary ==="
if [[ $FAILED -eq 0 ]]; then
    echo "All ${#TAPES[@]} screenshots generated successfully"
    exit 0
else
    echo "$FAILED of ${#TAPES[@]} screenshots failed"
    exit 1
fi
