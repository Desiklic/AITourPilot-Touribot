#!/bin/bash
# Dashboard startup script — used by com.touribot.dashboard LaunchAgent
# Ensures nvm node is on PATH and dashboard starts on port 4003

export PATH="/Users/hermannkudlich/.nvm/versions/node/v20.19.2/bin:$PATH"

TOURIBOT_HOME="/Users/hermannkudlich/Documents/ClaudeProjects/AITourPilot-Touribot"
DASHBOARD_DIR="$TOURIBOT_HOME/touri-dashboard"
LOG_DIR="$TOURIBOT_HOME/logs"
mkdir -p "$LOG_DIR"

# Load .env for API keys the dashboard API routes may need
if [ -f "$TOURIBOT_HOME/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$TOURIBOT_HOME/.env"
  set +a
fi

# Export TOURIBOT_HOME so Next.js API routes can find the databases
export TOURIBOT_HOME

# Filter out noisy per-request dev logs (polling endpoints flood the terminal)
npm --prefix "$DASHBOARD_DIR" run dev -- --port 4003 2>&1 \
  | grep -v --line-buffered -E '^ (GET|POST) /api/(chat/messages|chat/sessions|memory|settings)\b'
