#!/bin/bash
sleep 2
cd /yjs-server

# Install dependencies only if needed
if [ ! -d node_modules ] || [ ! -f node_modules/.package-lock.json ]; then
    echo "node_modules missing or incomplete, running npm install..."
    npm install
elif [ package-lock.json -nt node_modules/.install-stamp ] 2>/dev/null; then
    echo "package-lock.json changed, running npm install..."
    npm install
else
    echo "node_modules up to date, skipping npm install."
fi
touch node_modules/.install-stamp 2>/dev/null || true

# Check if running in production mode
if [ "$NODE_ENV" = "production" ]; then
    echo "Starting YJS in PRODUCTION mode..."
    npm run start
else
    echo "Starting YJS in DEVELOPMENT mode..."
    npm run dev -- --host
fi
