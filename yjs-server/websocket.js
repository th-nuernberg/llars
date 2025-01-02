const Y = require('yjs');
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
    
    socket.on('join_room', (data) => {
      const { username, room } = data;
      console.log(`User "${username}" joined room "${room}"`);
      
      socket.join(room);
      const doc = getOrCreateDoc(room);
      const roomObj = getOrCreateRoom(room);
      
      // Weise dem Benutzer eine Farbe zu
      const userColor = getRandomColor();
      roomObj.users[socket.id] = {
        username,
        color: userColor
      };
      
      // Sende den vollständigen State
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
      const doc = getOrCreateDoc(room);
      
      try {
        const uint8Update = new Uint8Array(update);
        Y.applyUpdate(doc, uint8Update);
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
        roomObj.cursors[socket.id] = {
          blockId,
          range,
          username: user.username,
          color: user.color
        };
        
        // Broadcast nur an andere Clients im Raum
        socket.to(room).emit('cursor_updated', {
          userId: socket.id,
          cursor: roomObj.cursors[socket.id]
        });
      }
    });
    
    socket.on('request_room_state', (room) => {
      const roomObj = getOrCreateRoom(room);
      socket.emit('room_state', {
        users: roomObj.users,
        cursors: roomObj.cursors
      });
    });
    
    socket.on('leave_room', (room) => {
      handleUserLeave(socket, room);
    });
    
    socket.on('disconnect', () => {
      console.log(`[-] Client disconnected: ${socket.id}`);
      
      // Entferne den Nutzer aus allen Räumen
      Object.keys(rooms).forEach(roomName => {
        handleUserLeave(socket, roomName);
      });
    });
  });
}

function handleUserLeave(socket, room) {
  socket.leave(room);
  const roomObj = rooms[room];
  
  if (roomObj) {
    delete roomObj.users[socket.id];
    delete roomObj.cursors[socket.id];
    
    // Informiere andere Benutzer
    socket.to(room).emit('user_left', {
      userId: socket.id
    });
    
    // Räume den Raum auf, wenn er leer ist
    if (Object.keys(roomObj.users).length === 0) {
      delete rooms[room];
      ydocs.delete(room);
    }
  }
}

module.exports = setupSocketHandlers;