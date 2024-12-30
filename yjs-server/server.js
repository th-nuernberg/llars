// server.js
const express = require('express');
const http = require('http');
const cors = require('cors');
const { Server } = require('socket.io');
const setupSocketHandlers = require('./websocket'); // Importiere die Socket-Logik

// Express-App erzeugen
const app = express();
app.use(cors()); // nur nötig, falls du CORS brauchst

// HTTP-Server erzeugen
const server = http.createServer(app);

// Socket.IO an den HTTP-Server binden
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  },
  path: '/collab/socket.io/'
});

// Setup der Socket.IO-Handler
setupSocketHandlers(io);

// Server starten
const PORT = process.env.PORT || 8082;
server.listen(PORT, () => {
  console.log(`✅ Server is running on port ${PORT}`);
});
