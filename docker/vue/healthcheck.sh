#!/bin/sh
# Healthcheck using Node.js (no curl needed on slim image)
node -e "
const http = require('http');
http.get('http://localhost:5173', r => {
  process.exit(r.statusCode === 200 ? 0 : 1);
}).on('error', () => process.exit(1));
"
