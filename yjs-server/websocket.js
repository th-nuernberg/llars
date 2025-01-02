// websocket.js
const Y = require('yjs');
const { logRoomsAndUsers, printYDoc } = require('./utils');

/**
 * Yjs-Dokumente für jede Room-Id
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
 * Initialisiert beispielhafte Blöcke mit Startwerten.
 */
function getOrCreateDoc(roomName) {
  if (!ydocs.has(roomName)) {
    const doc = new Y.Doc();

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
     *  - Wir schicken dem neuen User den aktuellen Yjs-Stand (snapshot_document)
     */
    socket.on('join_room', (data) => {
      const { username, room } = data;
      console.log(`User "${username}" joined room "${room}"`);

      // 1) Socket.io-Raum beitreten
      socket.join(room);

      // 2) Yjs-Dokument holen
      const doc = getOrCreateDoc(room);

      // 3) Update unserer Room-Verwaltung
      const roomObj = getOrCreateRoom(room);
      roomObj.users[socket.id] = username;

      // 4) Sende den vollständigen State an den neu verbundenen Client
      const fullState = Y.encodeStateAsUpdate(doc);
      socket.emit('snapshot_document', fullState);
      console.log(`[+] Sent full document state to ${socket.id}`);
      printYDoc(doc);

      // 5) Schicke dem neuen Client auch die aktuellen Cursors & Userliste
      socket.emit('room_state', {
        users: roomObj.users,
        cursors: roomObj.cursors
      });

      // Optional: andere im Raum informieren
      socket.to(room).emit('user_joined', {
        userId: socket.id,
        username
      });

      // Logge Räume und Benutzer
      logRoomsAndUsers(io);
    });

    /**
     * sync_update:
     *  - Empfängt ein Y-Update (Uint8Array) vom Client
     *  - Wendet das Update an unserem Doc an
     *  - Broadcastet an alle anderen Clients im selben Raum
     */
    socket.on('sync_update', (data) => {
      const { room, update } = data;
      console.log(`[+] sync_update in room "${room}" from ${socket.id}`);

      const doc = getOrCreateDoc(room);
      try {
        // Array zurück in ein Uint8Array
        const uint8Update = new Uint8Array(update);

        // Update anwenden
        Y.applyUpdate(doc, uint8Update);

        // Debug: Aktuellen Zustand im Server-Log zeigen
        const blocksMap = doc.getMap('blocks');
        blocksMap.forEach((value, key) => {
          const content = value.get('content');
          console.log(`Block ${key} content after update:`, content?.toString());
        });

        // Sende das Update an alle anderen im Raum
        socket.to(room).emit('sync_update', { update });
      } catch (error) {
        console.error('Error applying update:', error);
      }
    });

    /**
     * cursor_update:
     *  - Aktualisiert die Cursor-Position des Users
     *  - Broadcastet die neuen Cursor-Daten an alle im Raum
     */
    socket.on('cursor_update', (data) => {
      const { room, block_id, position } = data;
      const roomObj = getOrCreateRoom(room);

      const username = roomObj.users[socket.id] || 'Unknown';
      roomObj.cursors[socket.id] = {
        block_id,
        position,
        username
      };

      io.in(room).emit('cursor_updated', { cursors: roomObj.cursors });
    });

    /**
     * request_room_state:
     *  - Schickt dem anfragenden Client nochmals die User- und Cursor-Liste
     */
    socket.on('request_room_state', (room) => {
      const roomObj = getOrCreateRoom(room);
      socket.emit('room_state', {
        users: roomObj.users,
        cursors: roomObj.cursors
      });
    });

    /**
     * leave_room:
     *  - Benutzer verlässt den Raum
     */
    socket.on('leave_room', (room) => {
      socket.leave(room);
      const roomObj = rooms[room];
      if (roomObj) {
        delete roomObj.users[socket.id];
        delete roomObj.cursors[socket.id];

        io.in(room).emit('user_left', {
          userId: socket.id
        });

        // Falls Raum leer, löschen
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
     */
    socket.on('disconnect', () => {
      console.log(`[-] Client disconnected: ${socket.id}`);

      // Entferne den Nutzer aus allen Räumen, in denen er war
      for (const [roomName, roomObj] of Object.entries(rooms)) {
        if (roomObj.users[socket.id]) {
          delete roomObj.users[socket.id];
          delete roomObj.cursors[socket.id];

          io.in(roomName).emit('user_left', {
            userId: socket.id
          });

          // Falls Raum leer
          if (Object.keys(roomObj.users).length === 0) {
            delete rooms[roomName];
            ydocs.delete(roomName);
          }
        }
      }

      logRoomsAndUsers(io);
    });
  });
}

module.exports = setupSocketHandlers;
