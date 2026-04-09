#!/bin/bash
# FastAPI chat backend startup — used by com.touribot.api LaunchAgent
# Starts the uvicorn server on port 8766

TOURIBOT_HOME="/Users/hermannkudlich/Documents/ClaudeProjects/AITourPilot-Touribot"
PYTHON="/Users/hermannkudlich/Documents/Miniforge3/envs/comfyenv/bin/python"
LOG_DIR="$TOURIBOT_HOME/logs"
mkdir -p "$LOG_DIR"

# Load .env for ANTHROPIC_API_KEY and other secrets
if [ -f "$TOURIBOT_HOME/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$TOURIBOT_HOME/.env"
  set +a
fi

export TOURIBOT_HOME

cd "$TOURIBOT_HOME" || exit 1
exec "$PYTHON" -m uvicorn tools.api.server:app --host 127.0.0.1 --port 8766
