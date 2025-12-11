#!/bin/bash
sleep 2
cd /yjs-server

npm install

# Check if running in production mode
if [ "$NODE_ENV" = "production" ]; then
    echo "Starting YJS in PRODUCTION mode..."
    npm run start
else
    echo "Starting YJS in DEVELOPMENT mode..."
    npm run dev -- --host
fi