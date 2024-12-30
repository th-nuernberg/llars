// websocket.js
const Y = require('yjs');
const { logRoomsAndUsers, printYDoc } = require('./utils');

/**
 * Yjs-Dokumente für jede Room-Id (ähnlich wie in deinem Beispiel).
 * Map: roomName -> Y.Doc
 */
const ydocs = new Map();

/**
 * Raum-Verwaltung
 * Struktur:
 * rooms[roomName] = {
 *   users: { [socketId]: username },
 *   cursors: { [socketId]: { block_id, position, username } }
 * };
 */
const rooms = {};

/**
 * getOrCreateDoc(roomName):
 * Erstellt ein neues Y.Doc, falls noch nicht vorhanden.
 * Initialisiert beispielhafte Blöcke, damit wir Startwerte haben.
 */
function getOrCreateDoc(roomName) {
  if (!ydocs.has(roomName)) {
    const doc = new Y.Doc();

    // Beispiel-Inhalt, so wie in deinem Code
    doc.transact(() => {
      const blocksMap = doc.getMap('blocks');

      // Block 1
      const llmRoleDefMap = new Y.Map();
      llmRoleDefMap.set('title', 'LLM Role Definition');
      llmRoleDefMap.set('position', 1);
      const llmRoleContent = new Y.Text();
      llmRoleContent.insert(0, 'Defines the role...');
      llmRoleDefMap.set('content', llmRoleContent);
      blocksMap.set('LLM Role Definition', llmRoleDefMap);

      // Block 2
      const contextMap = new Y.Map();
      contextMap.set('title', 'Context');
      contextMap.set('position', 2);
      const contextContent = new Y.Text();
      contextContent.insert(0, 'Provides contextual info...');
      contextMap.set('content', contextContent);
      blocksMap.set('Context', contextMap);
    });

    ydocs.set(roomName, doc);
  }

  return ydocs.get(roomName);
}

/**
 * getOrCreateRoom(roomName):
 * Legt einen neuen Eintrag in 'rooms' an, falls er nicht existiert.
 */
function getOrCreateRoom(roomName) {
  if (!rooms[roomName]) {
    rooms[roomName] = {
      users: {},    // socketId -> username
      cursors: {}   // socketId -> { block_id, position, username }
    };
  }
  return rooms[roomName];
}

/**
 * setupSocketHandlers:
 * Richtet alle Socket.IO-Events ein.
 */
function setupSocketHandlers(io) {
  io.on('connection', (socket) => {
    console.log(`[+] Client connected: ${socket.id}`);

    // Optional: Logge aktuelle Räume und ihre Mitglieder
    logRoomsAndUsers(io);

    /**
     * join_room:
     *  - User tritt einem bestimmten Raum bei
     *  - Wir holen/erstellen den Y.Doc
     *  - Wir speichern den User in rooms[room].users
     *  - Wir schicken dem neuen User den aktuellen Yjs-Stand
     */
    socket.on('join_room', (data) => {
      const { username, room } = data;
      console.log(`User "${username}" joined room "${room}"`);

      // 1) Raum (im Sinne von socket.io) beitreten
      socket.join(room);

      // 2) Hole den Y.Doc für diesen Raum
      const doc = getOrCreateDoc(room);

      // 3) Update unsere Room-Verwaltung (users)
      const roomObj = getOrCreateRoom(room);
      roomObj.users[socket.id] = username;

      // 4) Schicke dem neu verbundenen Client den aktuellen Doc-State
      const fullState = Y.encodeStateAsUpdate(doc);
      socket.emit('update_document', fullState);
      console.log(`[+] Sent full document state to ${socket.id}`);
      printYDoc(doc);//

      // 5) Schicke dem neu verbundenen Client auch die aktuellen Cursors & Userliste
      socket.emit('room_state', {
        users: roomObj.users,
        cursors: roomObj.cursors
      });

      // Optional: Informiere andere im Raum, dass jemand neu reingekommen ist
      socket.to(room).emit('user_joined', {
        userId: socket.id,
        username: username
      });

      // Logge Räume und Benutzer
      logRoomsAndUsers(io);
    });

    /**
     * document_update:
     *  - Empfängt ein Y-Update (Uint8Array) vom Client
     *  - Wendet das Update an unserem Doc an
     *  - Broadcastet an alle anderen Clients im selben Raum
     */
    socket.on('document_update', (data) => {
  const { room, update } = data;
  console.log(`[+] Document update in room "${room}" from ${socket.id}`);

  // Hole das Doc
  const doc = getOrCreateDoc(room);

  try {
    // Wichtig: Konvertiere das Array zurück in ein Uint8Array
    const uint8Update = new Uint8Array(update);

    // Wende das Update an
    Y.applyUpdate(doc, uint8Update);

    // Debug: Zeige den aktuellen Zustand
    const blocksMap = doc.getMap('blocks');
    blocksMap.forEach((value, key) => {
      const content = value.get('content');
      console.log(`Block ${key} content after update:`, content?.toString());
    });

    // Sende das Update an alle anderen Clients
    socket.to(room).emit('document_update', { update });

  } catch (error) {
    console.error('Error applying update:', error);
  }
});

    /**
     * cursor_update:
     *  - Aktualisiert die Cursor-Position des Users in 'rooms[room].cursors[socket.id]'
     *  - Broadcastet die neuen Cursor-Daten an alle im Raum
     */
    socket.on('cursor_update', (data) => {
      const { room, block_id, position } = data;
      const roomObj = getOrCreateRoom(room);

      // Speichere Cursor
      const username = roomObj.users[socket.id] || 'Unknown';
      roomObj.cursors[socket.id] = {
        block_id,
        position,
        username
      };

      // An alle anderen im Raum senden (inkl. dem, der es geschickt hat,
      // falls du in der UI zeigen willst, wo der eigene Cursor ist –
      // aber meistens macht man `to(room).emit(...)` exklusiv ohne self).
      io.in(room).emit('cursor_updated', { cursors: roomObj.cursors });
    });

    /**
     * request_room_state:
     *  - Falls ein Client irgendwann nochmal den kompletten Zustand abrufen möchte
     *    (User-Liste, Cursor-Liste, etc.).
     */
    socket.on('request_room_state', (room) => {
      const roomObj = getOrCreateRoom(room);

      // Schicke den kompletten Room-Zustand (Users, Cursors)
      socket.emit('room_state', {
        users: roomObj.users,
        cursors: roomObj.cursors
      });
    });

    /**
     * leave_room:
     *  - Benutzer verlässt den Raum (auf eigenen Wunsch)
     */
    socket.on('leave_room', (room) => {
      socket.leave(room);
      const roomObj = rooms[room];
      if (roomObj) {
        // User aus dem Raum-Objekt entfernen
        delete roomObj.users[socket.id];
        delete roomObj.cursors[socket.id];

        // Den anderen Bescheid geben
        io.in(room).emit('user_left', {
          userId: socket.id
        });

        // Wenn keine User mehr im Raum, könnte man den Raum aus 'rooms' und 'ydocs' entfernen
        if (Object.keys(roomObj.users).length === 0) {
          delete rooms[room];
          ydocs.delete(room);
        }
      }
      console.log(`[+] User ${socket.id} left room "${room}"`);
    });

    /**
     * disconnect:
     *  - Wird aufgerufen, wenn ein Client seine Verbindung kappt.
     *    Dann entfernen wir ihn aus allen Räumen, in denen er ist.
     */
    socket.on('disconnect', () => {
      console.log(`[-] Client disconnected: ${socket.id}`);

      // Gehe alle Rooms durch und entferne den Nutzer daraus
      for (const [roomName, roomObj] of Object.entries(rooms)) {
        if (roomObj.users[socket.id]) {
          // 1) User entfernen
          delete roomObj.users[socket.id];
          delete roomObj.cursors[socket.id];

          // 2) Broadcasten, dass er weg ist
          io.in(roomName).emit('user_left', {
            userId: socket.id
          });

          // 3) Falls Raum jetzt leer, räumen wir auf
          if (Object.keys(roomObj.users).length === 0) {
            delete rooms[roomName];
            ydocs.delete(roomName);
          }
        }
      }

      // Nochmal: Logge Räume und Benutzer
      logRoomsAndUsers(io);
    });
  });
}

module.exports = setupSocketHandlers;


