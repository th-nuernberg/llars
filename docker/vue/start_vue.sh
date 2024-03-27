#!/bin/bash

# Navigate to the conversation-ranker directory
cd /vue

npm install
# npm audit fix
npm run dev -- --host
# npm run dev --host