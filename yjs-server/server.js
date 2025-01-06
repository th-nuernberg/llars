// server.js
const express = require('express');
const http = require('http');
const cors = require('cors');
const { Server } = require('socket.io');
const setupSocketHandlers = require('./websocket');

// Test-Funktion
const { testDBConnection } = require('./db/testDB');

const app = express();
app.use(cors());

// HTTP-Server
const server = http.createServer(app);

// Socket.IO
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  },
  path: '/collab/socket.io/'
});

// Aufruf der Socket-Logik
setupSocketHandlers(io);

// Starte Server
const PORT = process.env.PORT || 8082;
server.listen(PORT, async () => {
  console.log(`✅ Server is running on port ${PORT}`);

  // Hier mal kurz DB checken
  await testDBConnection();
});
