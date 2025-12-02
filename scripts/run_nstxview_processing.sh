#!/bin/bash
#
# NSTXView Paper Processing - Background Runner
#
# This script runs the paper processing pipeline in the background,
# with automatic rate limit handling and progress logging.
#
# Usage:
#   ./scripts/run_nstxview_processing.sh          # Process all pending papers
#   ./scripts/run_nstxview_processing.sh --limit 100  # Process 100 papers
#   ./scripts/run_nstxview_processing.sh --status  # Check current status
#
# The script runs with nohup so it survives terminal disconnection.
# Output is logged to: logs/nstxview_processing_YYYYMMDD_HHMMSS.log
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
BATCH_SIZE=20  # Process in batches to handle rate limits gracefully
PAUSE_BETWEEN_BATCHES=30  # Seconds to pause between batches

# Python path (use python3 explicitly for nohup environment)
PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

# Database URL for dev environment
export DATABASE_URL="postgresql://postgres:REDACTED_RAILWAY_PASSWORD@hopper.proxy.rlwy.net:32217/railway"

# Google credentials
export GOOGLE_APPLICATION_CREDENTIALS="/Users/rachelkremen/Documents/Code/NSTXView/talesai111-c6195629d677.json"

# Create logs directory
mkdir -p "$LOG_DIR"

# Generate log filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/nstxview_processing_$TIMESTAMP.log"

# Parse arguments
LIMIT=""
STATUS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --status)
            STATUS_ONLY=true
            shift
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to show status
show_status() {
    cd "$PROJECT_ROOT"
    $PYTHON scripts/process_nstxview_papers.py --status
}

# If status only, show and exit
if [ "$STATUS_ONLY" = true ]; then
    show_status
    exit 0
fi

# Check if another processing job is running
PID_FILE="$LOG_DIR/nstxview_processing.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Another processing job is already running (PID: $OLD_PID)"
        echo "Check logs at: $LOG_DIR/nstxview_processing_*.log"
        echo "To stop it: kill $OLD_PID"
        exit 1
    fi
fi

# Function to run processing
run_processing() {
    cd "$PROJECT_ROOT"

    echo "=============================================="
    echo "NSTXView Paper Processing Started"
    echo "Time: $(date)"
    echo "Batch size: $BATCH_SIZE"
    echo "Pause between batches: ${PAUSE_BETWEEN_BATCHES}s"
    if [ -n "$LIMIT" ]; then
        echo "Total limit: $LIMIT"
    fi
    echo "=============================================="
    echo ""

    # Show initial status
    $PYTHON scripts/process_nstxview_papers.py --status
    echo ""

    TOTAL_PROCESSED=0
    TOTAL_ERRORS=0
    BATCH_NUM=0

    while true; do
        BATCH_NUM=$((BATCH_NUM + 1))

        # Calculate remaining if limit is set
        if [ -n "$LIMIT" ]; then
            REMAINING=$((LIMIT - TOTAL_PROCESSED))
            if [ "$REMAINING" -le 0 ]; then
                echo "Reached limit of $LIMIT papers"
                break
            fi
            CURRENT_BATCH=$((REMAINING < BATCH_SIZE ? REMAINING : BATCH_SIZE))
        else
            CURRENT_BATCH=$BATCH_SIZE
        fi

        echo ""
        echo "--- Batch $BATCH_NUM: Processing up to $CURRENT_BATCH papers ---"
        echo "Time: $(date)"

        # Run extraction for this batch
        OUTPUT=$($PYTHON scripts/process_nstxview_papers.py --extract --limit "$CURRENT_BATCH" 2>&1)
        echo "$OUTPUT"

        # Check if we processed any papers
        if echo "$OUTPUT" | grep -q "Found 0 pending papers"; then
            echo "No more pending papers to process!"
            break
        fi

        # Extract success/error counts from output
        SUCCESS=$(echo "$OUTPUT" | grep "Processing complete" | sed 's/.*Success: \([0-9]*\).*/\1/' || echo "0")
        ERRORS=$(echo "$OUTPUT" | grep "Processing complete" | sed 's/.*Errors: \([0-9]*\).*/\1/' || echo "0")

        TOTAL_PROCESSED=$((TOTAL_PROCESSED + SUCCESS))
        TOTAL_ERRORS=$((TOTAL_ERRORS + ERRORS))

        echo "Batch $BATCH_NUM complete. Running total: $TOTAL_PROCESSED processed, $TOTAL_ERRORS errors"

        # Check if we should continue
        if [ "$SUCCESS" -eq 0 ] && [ "$ERRORS" -eq 0 ]; then
            echo "No papers processed in this batch, stopping"
            break
        fi

        # Pause between batches to avoid rate limits
        echo "Pausing ${PAUSE_BETWEEN_BATCHES}s before next batch..."
        sleep "$PAUSE_BETWEEN_BATCHES"
    done

    echo ""
    echo "=============================================="
    echo "Processing Complete!"
    echo "Time: $(date)"
    echo "Total processed: $TOTAL_PROCESSED"
    echo "Total errors: $TOTAL_ERRORS"
    echo "=============================================="
    echo ""

    # Show final status
    $PYTHON scripts/process_nstxview_papers.py --status
}

# Run in background with nohup
echo "Starting NSTXView paper processing in background..."
echo "Log file: $LOG_FILE"
echo ""

# Save PID
echo $$ > "$PID_FILE"

# Run the processing (this will be backgrounded by the caller using nohup)
run_processing >> "$LOG_FILE" 2>&1

# Clean up PID file
rm -f "$PID_FILE"

echo "Processing complete. Check log file for details."
