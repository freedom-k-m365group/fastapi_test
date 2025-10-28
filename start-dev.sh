#!/usr/bin/env bash
# start-dev.sh
# Runs: fastapi dev app/app.py  (foreground, reload)
#       celery worker           (background)

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No

echo -e "${GREEN}Starting FastAPI in DEV mode...${NC}"

# Start FastAPI in dev mode (foreground with auto-reload)
fastapi dev app/app.py --host 0.0.0.0 --port 8000 &

# Capture FastAPI PID
FASTAPI_PID=$!
echo "FastAPI (dev) PID: $FASTAPI_PID"

# Start Celery worker in background
echo -e "${GREEN}Starting Celery worker...${NC}"
celery -A app.celery.celery worker --loglevel=info > celery.log 2>&1 &
CELERY_PID=$!
echo "Celery PID: $CELERY_PID"

# Save PIDs for stop script
echo "$FASTAPI_PID" > .pids.dev
echo "$CELERY_PID" >> .pids.dev

echo -e "${GREEN}Both services started!${NC}"
echo "   FastAPI: http://localhost:8000"
echo "   Logs: tail -f celery.log"
echo "   Stop: ./stop-all.sh"

# Keep script alive until FastAPI exits (Ctrl+C will kill both)
wait $FASTAPI_PID