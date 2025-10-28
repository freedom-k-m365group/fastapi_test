#!/usr/bin/env bash
# stop-all.sh
# Kills any running FastAPI + Celery from start-dev.sh or start-prod.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

kill_pids() {
  local file=$1
  local name=$2
  if [[ -f "$file" ]]; then
    echo -e "${GREEN}Stopping $name processes...${NC}"
    while IFS= read -r pid; do
      if ps -p "$pid" > /dev/null 2>&1; then
        echo "Killing PID $pid ($name)"
        kill "$pid" 2>/dev/null || true
        # Force kill if still alive after 5s
        sleep 2
        if ps -p "$pid" > /dev/null 2>&1; then
          kill -9 "$pid" 2>/dev/null || true
        fi
      else
        echo "PID $pid already gone"
      fi
    done < "$file"
    rm -f "$file"
  else
    echo "No $name PID file found ($file)"
  fi
}

# Stop dev
kill_pids ".pids.dev" "Dev (FastAPI + Celery)"

# Stop prod
kill_pids ".pids.prod" "Prod (FastAPI + Celery)"

# Also kill any stray celery/uvicorn just in case
echo -e "${GREEN}Cleaning up stray processes...${NC}"
pkill -f "celery.*worker" || true
pkill -f "fastapi (dev|run)" || true

echo -e "${GREEN}All services stopped.${NC}"