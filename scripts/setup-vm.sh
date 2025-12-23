#!/bin/bash
# setup-vm.sh - Set up the benchmark tool on the VM
#
# Run this script on the VM after SSH'ing in.
# Usage: ./scripts/setup-vm.sh

set -e

echo "=========================================="
echo "Setting up Azure DB ZR Benchmark Tool"
echo "=========================================="
echo ""

# Check if running on Linux
if [[ "$(uname)" != "Linux" ]]; then
    echo "This script is intended to run on the benchmark VM (Linux)"
    exit 1
fi

# Create working directory
WORK_DIR="/opt/benchmark"
if [ ! -d "$WORK_DIR" ]; then
    sudo mkdir -p "$WORK_DIR"
    sudo chown "$USER:$USER" "$WORK_DIR"
fi

cd "$WORK_DIR"

# Clone the repository if not already present
if [ ! -d "azure-db-zr-bench" ]; then
    echo "Cloning repository..."
    git clone https://github.com/arsenvlad/azure-db-zr-bench.git
fi

cd azure-db-zr-bench

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the benchmark tool
echo "Installing benchmark tool..."
pip install -e .

# Verify installation
echo ""
echo "Verifying installation..."
azure-db-zr-bench --help

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment:"
echo "  cd $WORK_DIR/azure-db-zr-bench"
echo "  source .venv/bin/activate"
echo ""
echo "To set the database password:"
echo "  export DB_PASSWORD='your-password'"
echo ""
echo "To list available targets:"
echo "  azure-db-zr-bench list --config config.yaml"
echo ""
echo "To run a benchmark:"
echo "  azure-db-zr-bench run --target pg-noha --concurrency 4 --duration 300"
echo ""
echo "To run a full suite:"
echo "  azure-db-zr-bench suite --service postgres --concurrency 1,4,16 --duration 300"
