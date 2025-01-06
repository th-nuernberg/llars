#!/bin/bash
sleep 2
cd /yjs-server

npm install
# npm audit fix
npm run dev -- --host