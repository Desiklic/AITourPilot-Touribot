#!/bin/bash
# TouriBot Dashboard Startup Script
# Starts both Next.js dev server and FastAPI chat backend

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$DIR")"

echo "Starting TouriBot Dashboard..."
echo "  Next.js: http://localhost:4003"
echo "  FastAPI: http://localhost:8766"
echo ""

# Start FastAPI in background
cd "$PROJECT_ROOT"
python -m uvicorn tools.api.server:app --host 127.0.0.1 --port 8766 &
FASTAPI_PID=$!

# Start Next.js dev server
cd "$DIR"
npm run dev -- --port 4003 &
NEXTJS_PID=$!

# Trap to kill both on exit
trap "kill $FASTAPI_PID $NEXTJS_PID 2>/dev/null" EXIT

echo "Press Ctrl+C to stop both servers."
wait
