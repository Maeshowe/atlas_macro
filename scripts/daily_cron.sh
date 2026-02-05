#!/bin/bash
# ATLAS MACRO - Daily diagnostic script
# Run after US market close (4:30 PM EST / 22:30 CET)
#
# Crontab setup (run: crontab -e):
#   30 22 * * 1-5 /home/safrtam/atlas_macro/scripts/daily_cron.sh

set -e

# Configuration
PROJECT_DIR="/home/safrtam/atlas_macro"
LOG_DIR="${PROJECT_DIR}/logs"
DATE=$(date +%Y-%m-%d)

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Activate virtual environment if exists
if [ -f "${PROJECT_DIR}/.venv/bin/activate" ]; then
    source "${PROJECT_DIR}/.venv/bin/activate"
fi

# Log start
echo "========================================" >> "${LOG_DIR}/daily.log"
echo "[${DATE}] Starting ATLAS MACRO diagnostic" >> "${LOG_DIR}/daily.log"

# Run pipeline
cd "${PROJECT_DIR}"
PYTHONPATH=src python scripts/run_daily.py -v >> "${LOG_DIR}/daily.log" 2>&1

# Log completion
echo "[${DATE}] Diagnostic completed" >> "${LOG_DIR}/daily.log"
echo "========================================" >> "${LOG_DIR}/daily.log"
