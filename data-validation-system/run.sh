#!/bin/bash
# run.sh - Helper script to run the data validation system

# Load environment variables
source .env

# Ensure required directories exist
mkdir -p data/input
mkdir -p data/output
mkdir -p logs

# Default values
DEFAULT_INPUT="data/input/leads.csv"
DEFAULT_OUTPUT="data/output/validated_leads.csv"
DEFAULT_SUMMARY="data/output/validation_summary.json"

# Get arguments or use defaults
INPUT_FILE=${1:-$DEFAULT_INPUT}
OUTPUT_FILE=${2:-$DEFAULT_OUTPUT}
SUMMARY_FILE=${3:-$DEFAULT_SUMMARY}

# Create log filename with timestamp
LOG_FILE="logs/validation_$(date +%Y%m%d_%H%M%S).log"

echo "Starting data validation process..."
echo "Input file: $INPUT_FILE"
echo "Output file: $OUTPUT_FILE"
echo "Summary file: $SUMMARY_FILE"
echo "Log file: $LOG_FILE"

# Run the validation script
python main.py \
  --input "$INPUT_FILE" \
  --output "$OUTPUT_FILE" \
  --email "$CHATGPT_EMAIL" \
  --password "$CHATGPT_PASSWORD" \
  --batch-size ${BATCH_SIZE:-5} \
  --batch-mode ${BATCH_MODE:-single} \
  --summary "$SUMMARY_FILE" \
  ${USE_HEADLESS:+--headless} \
  2>&1 | tee -a "$LOG_FILE"

echo "Validation process completed. Check $OUTPUT_FILE for results and $SUMMARY_FILE for validation summary."