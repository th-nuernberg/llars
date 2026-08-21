#!/bin/bash

# Navigate to the Vue directory
cd /vue

# Install dependencies only if needed (volume mount may overwrite build-time node_modules)
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
if [ "$VITE_PROJECT_STATE" = "production" ] || [ "$NODE_ENV" = "production" ]; then
    echo "Starting in PRODUCTION mode..."
    # Build the production bundle
    npm run build
    # Serve the built files with vite preview
    npm run preview -- --host --port 5173
else
    echo "Starting in DEVELOPMENT mode..."
    npm run dev -- --host
fi
