// websocket.js
const Y = require('yjs');
const { logRoomsAndUsers, printYDoc } = require('./utils');

// Wir verwalten hier die YDocs im Speicher
const ydocs = new Map();

/**
 * Hilfsfunktion: Gibt eine existierende Y.Doc zurück
 * oder erzeugt eine neue, falls nicht vorhanden.
 */
function getOrCreateDoc(roomName) {
  if (!ydocs.has(roomName)) {
    const doc = new Y.Doc();

    doc.transact(() => {
      const blocksMap = doc.getMap('blocks');

      const llmRoleDefMap = new Y.Map();
      llmRoleDefMap.set('title', 'LLM Role Definition');
      llmRoleDefMap.set('position', 1);

      const llmRoleContent = new Y.Text();
      llmRoleContent.insert(0, 'Defines the role...');
      llmRoleDefMap.set('content', llmRoleContent);

      blocksMap.set('LLM Role Definition', llmRoleDefMap);

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

function setupSocketHandlers(io) {
  io.on('connection', (socket) => {
    console.log(`[+] Client connected: ${socket.id}`);

    // Logge aktuelle Räume und ihre Mitglieder
    logRoomsAndUsers(io);

    socket.on('join_room', (data) => {
      const { username, room } = data;
      console.log(`User "${username}" joined room "${room}"`);

      // Tritt dem Raum bei
      socket.join(room);

      // Lade das Dokument oder erstelle ein neues
      const doc = getOrCreateDoc(room);
      const fullState = Y.encodeStateAsUpdate(doc);
      socket.emit('update_document', fullState);

      // Logge aktuelle Räume und ihre Mitglieder
      logRoomsAndUsers(io);
    });

    socket.on('document_update', (data) => {
      const { room, update } = data;
      const doc = getOrCreateDoc(room);
      console.log(`[+] Document update in room "${room} from ${socket.id}`);

      // Wende Änderungen an und sende sie an andere Clients im Raum
      Y.applyUpdate(doc, update);
      socket.to(room).emit('document_update', update);
      console.log(`[+] Document update sent to room "${room}"`);
      printYDoc(doc);
    });

    socket.on('disconnect', () => {
      console.log(`[-] Client disconnected: ${socket.id}`);

      // Logge aktuelle Räume und ihre Mitglieder
      logRoomsAndUsers(io);
    });
  });
}

/**
 * Logge alle aktuellen Räume und die Benutzer, die sich in diesen Räumen befinden.
 */


module.exports = setupSocketHandlers;

