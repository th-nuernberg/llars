#!/bin/bash

# Navigate to the conversation-ranker directory
cd /vue

npm install
# npm audit fix
npm run dev -- --host
# nodemon --exec npm run dev -- --host
# nodemon
# npm run dev --host