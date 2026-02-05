#!/bin/bash
# ATLAS MACRO - Linux Server Deployment Script
#
# Usage: ./scripts/deploy_linux.sh
#
# Prerequisites:
#   - Python 3.11+
#   - Git

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== ATLAS MACRO Linux Deployment ===${NC}"

# Configuration - uses current directory
INSTALL_DIR="$(pwd)"
VENV_DIR="${INSTALL_DIR}/.venv"

echo "Install directory: ${INSTALL_DIR}"

# Step 1: Check Python version
echo -e "\n${GREEN}[1/6] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.11+ required. Found: ${PYTHON_VERSION}${NC}"
    exit 1
fi
echo "Python ${PYTHON_VERSION} OK"

# Step 2: Create virtual environment
echo -e "\n${GREEN}[2/6] Setting up virtual environment...${NC}"
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
    echo "Created virtual environment at ${VENV_DIR}"
else
    echo "Virtual environment already exists"
fi

# Activate venv
source "${VENV_DIR}/bin/activate"

# Step 3: Install dependencies
echo -e "\n${GREEN}[3/6] Installing dependencies...${NC}"
pip install --upgrade pip
pip install -e ".[dev]"

# Step 4: Create required directories
echo -e "\n${GREEN}[4/6] Creating data directories...${NC}"
mkdir -p "${INSTALL_DIR}/data/output"
mkdir -p "${INSTALL_DIR}/data/cache"
mkdir -p "${INSTALL_DIR}/logs"

# Step 5: Check for .env file
echo -e "\n${GREEN}[5/6] Checking configuration...${NC}"
if [ ! -f "${INSTALL_DIR}/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from template...${NC}"
    cp "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
    echo -e "${YELLOW}Please edit ${INSTALL_DIR}/.env with your API keys${NC}"
else
    echo ".env file found"
fi

# Step 6: Test installation
echo -e "\n${GREEN}[6/6] Testing installation...${NC}"
PYTHONPATH=src python -c "from atlas_macro.pipeline.daily import DailyPipeline; print('Import OK')" && echo "Installation successful!"

# Run tests
echo -e "\n${GREEN}Running tests...${NC}"
PYTHONPATH=src python -m pytest tests/ -v --tb=short

echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your API keys (POLYGON_KEY, FRED_KEY)"
echo "  2. Copy systemd files:"
echo "     sudo cp scripts/atlas-daily.service /etc/systemd/system/"
echo "     sudo cp scripts/atlas-daily.timer /etc/systemd/system/"
echo "     sudo cp scripts/atlas-dashboard.service /etc/systemd/system/"
echo "  3. Enable services:"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl enable --now atlas-daily.timer"
echo "     sudo systemctl enable --now atlas-dashboard"
echo "  4. Configure nginx for https://atlas.ssh.services"
echo ""
echo "Manual run: PYTHONPATH=src python scripts/run_daily.py -v"
