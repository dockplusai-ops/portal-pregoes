#!/bin/bash
echo "Starting PNCP sync worker (with auto-restart)..."

run_sync() {
    python3 /app/sync.py
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        echo "Sync exited with code $EXIT_CODE at $(date), retrying in 60s..."
    fi
    return $EXIT_CODE
}

# Rodar imediatamente
run_sync

# Loop principal
while true; do
    echo "Sleeping 15 minutes... ($(date))"
    sleep 900
    echo "Running sync at $(date)"
    run_sync || echo "Sync failed, continuing loop..."
done
