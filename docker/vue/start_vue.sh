#!/bin/bash

# Navigate to the Vue directory
cd /vue

# Install dependencies
npm install

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