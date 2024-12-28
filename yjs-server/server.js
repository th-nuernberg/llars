/**
 * server.js
 */
const express = require('express');
const http = require('http');
const cors = require('cors');
const { Server } = require('socket.io');
const Y = require('yjs');

// Express-App erzeugen
const app = express();
app.use(cors()); // nur nötig, falls du CORS brauchst

// HTTP-Server erzeugen
const server = http.createServer(app);

// Socket.IO an den HTTP-Server binden
const io = new Server(server, {
  cors: {
    origin: "*", // Hier ggf. deine eigene URL / Regex eingeben
    methods: ["GET", "POST"]
  }
});

// Wir verwalten hier die YDocs im Speicher:
// key = roomName, value = Y.Doc-Instanz
const ydocs = new Map();

/**
 * Hilfsfunktion: Gibt eine existierende Y.Doc zurück
 * oder erzeugt eine neue, falls nicht vorhanden.
 */
function getOrCreateDoc(roomName) {
  if (!ydocs.has(roomName)) {
    const newDoc = new Y.Doc();
    ydocs.set(roomName, newDoc);
  }
  return ydocs.get(roomName);
}

io.on('connection', (socket) => {
  console.log(`[+] Client connected: ${socket.id}`);

  // 1) Client tritt einem Raum bei
  //    Datenstruktur: { username: string, room: string }
  socket.on('join_room', (data) => {
    const { username, room } = data;
    console.log(`User "${username}" joined room "${room}"`);

    // Socket in Raum schalten
    socket.join(room);

    // YDoc für diesen Raum holen oder anlegen
    const doc = getOrCreateDoc(room);

    // Jetzt bekommt der neu beigetretene Client erstmal den
    // kompletten Stand (encoded State) des Docs
    const fullState = Y.encodeStateAsUpdate(doc);
    socket.emit('update_document', fullState);
  });

  // 2) Client sendet ein Update an den Server (alle Edits, Einfügungen etc.)
  //    Datenstruktur: { room: string, update: Uint8Array (als Buffer oder Base64) }
  socket.on('document_update', (data) => {
    const { room, update } = data;

    // Im Raum das entsprechende Doc holen
    const doc = getOrCreateDoc(room);

    // Das Update in das serverseitige Doc einspielen (so bleibt der Server auf dem aktuellen Stand)
    Y.applyUpdate(doc, update);

    // An alle anderen Clients im gleichen Raum verteilen (außer dem Sender selbst)
    socket.to(room).emit('document_update', update);
  });

  // 3) Optional: Wenn der Client die Verbindung trennt
  socket.on('disconnect', () => {
    console.log(`[-] Client disconnected: ${socket.id}`);
  });
});

// Server starten
const PORT = process.env.PORT || 8082;
server.listen(PORT, () => {
  console.log(`✅ Server is running on port ${PORT}`);
});
