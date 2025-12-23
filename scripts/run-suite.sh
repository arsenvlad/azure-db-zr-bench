#!/bin/bash
# run-suite.sh - Run a full benchmark suite
#
# Usage: ./scripts/run-suite.sh [service] [concurrency] [duration]
#
# Examples:
#   ./scripts/run-suite.sh                    # All services, default settings
#   ./scripts/run-suite.sh postgres           # PostgreSQL only
#   ./scripts/run-suite.sh all "1,4,16" 300   # All services, custom concurrency, 5 min

set -e

SERVICE="${1:-all}"
CONCURRENCY="${2:-1,4,16}"
DURATION="${3:-300}"
WARMUP="${4:-30}"
CONFIG="${CONFIG:-config.yaml}"

echo "=========================================="
echo "Azure DB ZR Benchmark Suite"
echo "=========================================="
echo ""
echo "Service:     $SERVICE"
echo "Concurrency: $CONCURRENCY"
echo "Duration:    ${DURATION}s"
echo "Warmup:      ${WARMUP}s"
echo "Config:      $CONFIG"
echo ""

# Check if DB_PASSWORD is set
if [ -z "$DB_PASSWORD" ]; then
    echo "Error: DB_PASSWORD environment variable is not set"
    echo "Run: export DB_PASSWORD='your-password'"
    exit 1
fi

# Run the benchmark suite
azure-db-zr-bench suite \
    --service "$SERVICE" \
    --config "$CONFIG" \
    --concurrency "$CONCURRENCY" \
    --duration "$DURATION" \
    --warmup "$WARMUP"

echo ""
echo "Suite completed!"
echo "Results are in the results/ directory"
echo ""
echo "To generate a comparison report:"
echo "  azure-db-zr-bench report --results results/"
