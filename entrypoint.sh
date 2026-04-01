#!/bin/bash
set -e

echo "Starting PNCP sync worker..."
echo "Will run sync every 15 minutes"

# Rodar imediatamente no início
python3 /app/sync.py

# Loop a cada 15 minutos
while true; do
    echo "Sleeping 15 minutes..."
    sleep 900
    echo "Running sync at $(date)"
    python3 /app/sync.py || echo "Sync failed, will retry in 15 minutes"
done
