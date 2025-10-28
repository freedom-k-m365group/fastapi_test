#!/usr/bin/env bash
# start-prod.sh
# Runs: fastapi run app/app.py  (foreground, no reload)
#       celery worker           (background, nohup + log)

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting FastAPI in PROD mode...${NC}"

# Start FastAPI in production mode
fastapi run app/app.py --host 0.0.0.0 --port 8000 &

FASTAPI_PID=$!
echo "FastAPI (prod) PID: $FASTAPI_PID"

# Start Celery with nohup so it survives terminal close
echo -e "${GREEN}Starting Celery worker (nohup)...${NC}"
nohup celery -A app.celery.celery worker --loglevel=info > celery.log 2>&1 &

CELERY_PID=$!
echo "Celery PID: $CELERY_PID"

# Save PIDs
echo "$FASTAPI_PID" > .pids.prod
echo "$CELERY_PID" >> .pids.prod

echo -e "${GREEN}Production services running!${NC}"
echo "   FastAPI: http://localhost:8000"
echo "   Logs: tail -f celery.log"
echo "   Stop: ./stop-all.sh"

wait $FASTAPI_PID