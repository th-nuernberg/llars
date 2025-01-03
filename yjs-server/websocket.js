// websocket.js
const Y = require('yjs');
const pool = require('./db/db'); // Verbindung zur Datenbank
const { logRoomsAndUsers, printYDoc } = require('./utils');

/**
 * Yjs-Dokumente für jede Room-Id
 * Map: roomName -> Y.Doc
 */
const ydocs = new Map();

/**
 * Raum-Verwaltung mit erweiterter Awareness
 * Struktur:
 * rooms[roomName] = {
 *   users: { [socketId]: { username, color } },
 *   cursors: { [socketId]: { blockId, range, username, color } }
 * };
 */
const rooms = {};

// Farbpalette für neue Benutzer
const COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
  '#FFEEAD', '#D4A5A5', '#9B59B6', '#3498DB'
];

function getRandomColor() {
  return COLORS[Math.floor(Math.random() * COLORS.length)];
}

// Funktion: Y.Doc zu JSON
function ydocToJson(doc) {
  const update = Y.encodeStateAsUpdate(doc);
  return JSON.stringify(Array.from(update));
}

// Funktion: JSON zu Y.Doc
function jsonToYdoc(jsonString) {
  const update = new Uint8Array(JSON.parse(jsonString));
  const doc = new Y.Doc();
  Y.applyUpdate(doc, update);
  return doc;
}

/**
 * Speichert das Y.Doc in der Datenbank für das gegebene prompt_id (= roomName).
 * - Falls bereits ein Eintrag existiert → UPDATE
 * - Falls nicht → INSERT
 *
 * @param {string|number} roomName  Raum-Name, in deinem Fall = prompt_id
 * @param {Y.Doc} doc              Das Yjs-Dokument
 * @param {string} name            Optionaler Prompt-Name
 * @param {number|null} userId     ID des Besitzers (kann auch null sein)
 */
async function saveYdocToDB(roomName, doc, name, userId) {
  // Entferne den Präfix "room_" aus der Raum-ID (falls vorhanden)
  const roomId = parseInt(roomName.replace(/^room_/, ''), 10);
  const jsonString = ydocToJson(doc);

  try {
    const [rows] = await pool.query(
      'SELECT prompt_id FROM user_prompts WHERE prompt_id = ?',
      [roomId]
    );

    if (rows.length > 0) {
      // Existiert bereits → UPDATE
      await pool.query(
        `UPDATE user_prompts
         SET content = ?, updated_at = NOW()
         WHERE prompt_id = ?`,
        [jsonString, roomId]
      );
    } else {
      // Noch nicht vorhanden → INSERT
      await pool.query(
        `INSERT INTO user_prompts (prompt_id, user_id, name, content, created_at, updated_at)
         VALUES (?, ?, ?, ?, NOW(), NOW())`,
        [roomId, userId, name || 'Untitled', jsonString]
      );
    }

    console.log(`Y.Doc für Raum ${roomName} (prompt_id=${roomId}) gespeichert.`);
  } catch (err) {
    console.error(`Fehler beim Speichern des Y.Doc für Raum ${roomName}:`, err);
  }
}

/**
 * Lädt das Y.Doc aus der Datenbank für das gegebene prompt_id (= roomName).
 * Gibt ein neues Y.Doc zurück, falls keins gefunden wurde.
 *
 * @param {string|number} roomName
 * @returns {Y.Doc}
 */
async function loadYdocFromDB(roomName) {
  try {
    const roomId = parseInt(roomName.replace(/^room_/, ''), 10);
    const [rows] = await pool.query(
      'SELECT content FROM user_prompts WHERE prompt_id = ?',
      [roomId]
    );

    if (rows.length > 0 && rows[0].content) {
      return jsonToYdoc(rows[0].content);
    }
  } catch (err) {
    console.error(`Fehler beim Laden des Y.Doc für Raum ${roomName}:`, err);
  }
  return new Y.Doc();
}

function getOrCreateRoom(roomName) {
  if (!rooms[roomName]) {
    rooms[roomName] = {
      users: {},    // socketId -> { username, color }
      cursors: {}   // socketId -> { blockId, range, username, color }
    };
  }
  return rooms[roomName];
}

function setupSocketHandlers(io) {
  io.on('connection', (socket) => {
    console.log(`[+] Client connected: ${socket.id}`);

    socket.on('join_room', async (data) => {
      const { username, room, userId } = data; // userId hinzugefügt
      console.log(`User "${username}" joined room "${room}"`);

      socket.join(room);
      let doc = ydocs.get(room);

      // Lade Y.Doc aus der Datenbank, wenn es noch nicht im Speicher ist
      if (!doc) {
        doc = await loadYdocFromDB(room);
        ydocs.set(room, doc);
      }

      const roomObj = getOrCreateRoom(room);

      // Weise dem Benutzer eine Farbe zu
      const userColor = getRandomColor();
      roomObj.users[socket.id] = {
        username,
        color: userColor
      };

      // Sende den vollständigen State (Schnappschuss)
      const fullState = Y.encodeStateAsUpdate(doc);
      socket.emit('snapshot_document', fullState);

      // Sende dem neuen Client die aktuellen Cursors & Userliste
      socket.emit('room_state', {
        users: roomObj.users,
        cursors: roomObj.cursors
      });

      // Informiere andere über den neuen Benutzer
      socket.to(room).emit('user_joined', {
        userId: socket.id,
        username,
        color: userColor
      });

      logRoomsAndUsers(io);
    });

    socket.on('sync_update', (data) => {
      const { room, update } = data;
      const doc = ydocs.get(room);
      try {
        const uint8Update = new Uint8Array(update);
        Y.applyUpdate(doc, uint8Update);
        // Optional: Debug-Ausgabe
        printYDoc(doc);

        // Weiterleiten an alle anderen Clients im Raum
        socket.to(room).emit('sync_update', { update });
      } catch (error) {
        console.error('Error applying update:', error);
      }
    });

    socket.on('cursor_update', (data) => {
      const { room, blockId, range } = data;
      const roomObj = getOrCreateRoom(room);
      const user = roomObj.users[socket.id];

      if (user) {
        if (range === null) {
          // Entferne den Cursor-Eintrag
          delete roomObj.cursors[socket.id];
          socket.to(room).emit('cursor_updated', { userId: socket.id, cursor: null });
        } else {
          // Aktualisiere den Cursor-Eintrag
          roomObj.cursors[socket.id] = {
            blockId,
            range,
            username: user.username,
            color: user.color
          };
          socket.to(room).emit('cursor_updated', {
            userId: socket.id,
            cursor: roomObj.cursors[socket.id]
          });
        }
      }
    });

    socket.on('leave_room', (room) => {
      handleUserLeave(socket, room);
    });

    socket.on('disconnect', () => {
      console.log(`[-] Client disconnected: ${socket.id}`);

      // Entferne den Nutzer aus allen Räumen
      Object.keys(rooms).forEach((roomName) => {
        handleUserLeave(socket, roomName);
      });
    });
  });
}

async function handleUserLeave(socket, room) {
  socket.leave(room);
  const roomObj = rooms[room];

  if (roomObj) {
    delete roomObj.users[socket.id];
    delete roomObj.cursors[socket.id];

    // Informiere andere Benutzer
    socket.to(room).emit('user_left', { userId: socket.id });

    // Räume den Raum auf, wenn er leer ist
    if (Object.keys(roomObj.users).length === 0) {
      const doc = ydocs.get(room);
      if (doc) {
        // Beispiel: Raum-Name als Prompt-Name speichern
        // Wenn du einen anderen Namen willst, kannst du das anpassen
        await saveYdocToDB(room, doc, `Room ${room}`, null);
        ydocs.delete(room);
      }
      delete rooms[room];
    }
  }
}

module.exports = setupSocketHandlers;
