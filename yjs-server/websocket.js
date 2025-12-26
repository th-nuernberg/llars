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
const saveTimers = new Map();

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

function parseRoom(roomName) {
  if (typeof roomName !== 'string') return null;
  const promptMatch = roomName.match(/^room_(\d+)$/);
  if (promptMatch) {
    return { kind: 'prompt', id: parseInt(promptMatch[1], 10) };
  }
  const markdownMatch = roomName.match(/^markdown_(\d+)$/);
  if (markdownMatch) {
    return { kind: 'markdown', id: parseInt(markdownMatch[1], 10) };
  }
  const latexMatch = roomName.match(/^latex_(\d+)$/);
  if (latexMatch) {
    return { kind: 'latex', id: parseInt(latexMatch[1], 10) };
  }
  return null;
}

async function canAccessMarkdownDocument(documentId, username, isAdmin) {
  try {
    if (isAdmin) return true;
    if (!username) return false;

    const [rows] = await pool.query(
      `SELECT md.workspace_id AS workspace_id, mw.owner_username AS owner_username
       FROM markdown_documents md
       JOIN markdown_workspaces mw ON mw.id = md.workspace_id
       WHERE md.id = ?
       LIMIT 1`,
      [documentId]
    );

    if (!rows || rows.length === 0) return false;
    const workspaceId = rows[0].workspace_id;
    const ownerUsername = rows[0].owner_username;
    if (ownerUsername === username) return true;

    const [memberRows] = await pool.query(
      `SELECT 1
       FROM markdown_workspace_members
       WHERE workspace_id = ? AND username = ?
       LIMIT 1`,
      [workspaceId, username]
    );

    return !!(memberRows && memberRows.length > 0);
  } catch (e) {
    console.error(`[AuthZ] Failed to check markdown access for doc ${documentId}:`, e);
    return false;
  }
}

async function canAccessLatexDocument(documentId, username, isAdmin) {
  try {
    if (isAdmin) return true;
    if (!username) return false;

    const [rows] = await pool.query(
      `SELECT ld.workspace_id AS workspace_id, lw.owner_username AS owner_username
       FROM latex_documents ld
       JOIN latex_workspaces lw ON lw.id = ld.workspace_id
       WHERE ld.id = ?
       LIMIT 1`,
      [documentId]
    );

    if (!rows || rows.length === 0) return false;
    const workspaceId = rows[0].workspace_id;
    const ownerUsername = rows[0].owner_username;
    if (ownerUsername === username) return true;

    const [memberRows] = await pool.query(
      `SELECT 1
       FROM latex_workspace_members
       WHERE workspace_id = ? AND username = ?
       LIMIT 1`,
      [workspaceId, username]
    );

    return !!(memberRows && memberRows.length > 0);
  } catch (e) {
    console.error(`[AuthZ] Failed to check latex access for doc ${documentId}:`, e);
    return false;
  }
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
 * @param {string|null} username   Optional (für markdown_documents last_editor_username)
 */
async function saveYdocToDB(roomName, doc, name, userId, username = null) {
  const parsed = parseRoom(roomName);
  if (!parsed) return;

  const roomId = parsed.id;
  const jsonString = ydocToJson(doc);
  const textContent = (() => {
    try {
      return doc.getText('content').toString();
    } catch (e) {
      return '';
    }
  })();

  try {
    if (parsed.kind === 'prompt') {
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
      return;
    }

    if (parsed.kind === 'markdown') {
      const [rows] = await pool.query(
        'SELECT id FROM markdown_documents WHERE id = ?',
        [roomId]
      );

      if (rows.length === 0) {
        console.warn(`Markdown document ${roomId} not found; cannot persist Y.Doc for room ${roomName}`);
        return;
      }

      await pool.query(
        `UPDATE markdown_documents
         SET content = ?, updated_at = NOW(), last_editor_username = COALESCE(?, last_editor_username)
         WHERE id = ?`,
        [jsonString, username, roomId]
      );
      console.log(`Y.Doc für Raum ${roomName} (markdown_documents.id=${roomId}) gespeichert.`);
    }

    if (parsed.kind === 'latex') {
      const [rows] = await pool.query(
        'SELECT id FROM latex_documents WHERE id = ?',
        [roomId]
      );

      if (rows.length === 0) {
        console.warn(`Latex document ${roomId} not found; cannot persist Y.Doc for room ${roomName}`);
        return;
      }

      await pool.query(
        `UPDATE latex_documents
         SET content = ?, content_text = ?, updated_at = NOW(), last_editor_username = COALESCE(?, last_editor_username)
         WHERE id = ?`,
        [jsonString, textContent, username, roomId]
      );
      console.log(`Y.Doc für Raum ${roomName} (latex_documents.id=${roomId}) gespeichert.`);
    }
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
    const parsed = parseRoom(roomName);
    if (!parsed) return new Y.Doc();

    const roomId = parsed.id;

    if (parsed.kind === 'prompt') {
      const [rows] = await pool.query(
        'SELECT content FROM user_prompts WHERE prompt_id = ?',
        [roomId]
      );

      if (rows.length > 0 && rows[0].content) {
        return jsonToYdoc(rows[0].content);
      }
      return new Y.Doc();
    }

    if (parsed.kind === 'markdown') {
      const [rows] = await pool.query(
        'SELECT content FROM markdown_documents WHERE id = ?',
        [roomId]
      );
      if (rows.length > 0 && rows[0].content) {
        return jsonToYdoc(rows[0].content);
      }
      return new Y.Doc();
    }

    if (parsed.kind === 'latex') {
      const [rows] = await pool.query(
        'SELECT content, content_text FROM latex_documents WHERE id = ?',
        [roomId]
      );
      if (rows.length > 0) {
        if (rows[0].content) {
          return jsonToYdoc(rows[0].content);
        }
        if (rows[0].content_text) {
          const doc = new Y.Doc();
          doc.getText('content').insert(0, rows[0].content_text);
          return doc;
        }
      }
      return new Y.Doc();
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
    // Socket is already authenticated by middleware
    const authenticatedUser = socket.user;
    console.log(`[+] Client connected: ${socket.id} (User: ${authenticatedUser.username})`);

    socket.on('join_room', async (data) => {
      const { room } = data; // Nur room wird vom Client erwartet
      // Username und userId kommen aus dem authentifizierten Token (socket.user)
      const username = authenticatedUser.username;
      const userId = authenticatedUser.userId;

      console.log(`User "${username}" (${userId}) joined room "${room}"`);

      // Authorization for Markdown Collab rooms (prevents guessing document IDs)
      const parsed = parseRoom(room);
      if (parsed?.kind === 'markdown') {
        const allowed = await canAccessMarkdownDocument(parsed.id, username, authenticatedUser.isAdmin);
        if (!allowed) {
          console.warn(`[AuthZ] Denied access for user "${username}" to room "${room}"`);
          socket.emit('collab:error', { error: 'Forbidden' });
          socket.disconnect(true);
          return;
        }
      }
      if (parsed?.kind === 'latex') {
        const allowed = await canAccessLatexDocument(parsed.id, username, authenticatedUser.isAdmin);
        if (!allowed) {
          console.warn(`[AuthZ] Denied access for user "${username}" to room "${room}"`);
          socket.emit('collab:error', { error: 'Forbidden' });
          socket.disconnect(true);
          return;
        }
      }

      socket.join(room);
      let doc = ydocs.get(room);

      // Lade Y.Doc aus der Datenbank, wenn es noch nicht im Speicher ist
      if (!doc) {
        doc = await loadYdocFromDB(room);
        ydocs.set(room, doc);
      }

      const roomObj = getOrCreateRoom(room);

      // Use persisted color from handshake auth, or fall back to random color
      const userColor = socket.handshake?.auth?.color || getRandomColor();
      roomObj.users[socket.id] = {
        username,
        userId,
        color: userColor,
        isAdmin: authenticatedUser.isAdmin
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

        // Debounced persistence to reduce data-loss on server restarts.
        // (Prompt saving on empty-room remains as a final flush.)
        const existingTimer = saveTimers.get(room);
        if (existingTimer) clearTimeout(existingTimer);
        saveTimers.set(room, setTimeout(async () => {
          try {
            await saveYdocToDB(room, doc, `Room ${room}`, authenticatedUser.userId || null, authenticatedUser.username || null);
          } catch (e) {
            console.error(`Debounced save failed for room ${room}:`, e);
          } finally {
            saveTimers.delete(room);
          }
        }, 2000));
      } catch (error) {
        console.error('Error applying update:', error);
      }
    });

    socket.on('flush_document', async (data, callback) => {
      const room = data?.room;
      if (!room) {
        if (callback) callback({ success: false, error: 'room is required' });
        return;
      }

      const doc = ydocs.get(room);
      if (!doc) {
        if (callback) callback({ success: false, error: 'room not loaded' });
        return;
      }

      const existingTimer = saveTimers.get(room);
      if (existingTimer) {
        clearTimeout(existingTimer);
        saveTimers.delete(room);
      }

      try {
        await saveYdocToDB(room, doc, `Room ${room}`, authenticatedUser.userId || null, authenticatedUser.username || null);
        if (callback) callback({ success: true });
      } catch (e) {
        console.error(`Flush save failed for room ${room}:`, e);
        if (callback) callback({ success: false, error: String(e?.message || e) });
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

    // ============================================
    // Workspace Tree Updates (for MarkdownCollab)
    // ============================================

    // Join a workspace room to receive tree updates
    socket.on('join_workspace', async (data) => {
      const { workspaceId } = data;
      if (!workspaceId) return;

      const workspaceRoom = `workspace_${workspaceId}`;
      socket.join(workspaceRoom);
      console.log(`[Workspace] User "${authenticatedUser.username}" joined workspace room "${workspaceRoom}"`);
    });

    // Leave workspace room
    socket.on('leave_workspace', (data) => {
      const { workspaceId } = data;
      if (!workspaceId) return;

      const workspaceRoom = `workspace_${workspaceId}`;
      socket.leave(workspaceRoom);
      console.log(`[Workspace] User "${authenticatedUser.username}" left workspace room "${workspaceRoom}"`);
    });

    // Broadcast tree changes to all clients in the workspace
    socket.on('tree_node_created', (data) => {
      const { workspaceId, node, username } = data;
      if (!workspaceId || !node) return;

      const workspaceRoom = `workspace_${workspaceId}`;
      // Broadcast to all OTHER clients in the workspace
      socket.to(workspaceRoom).emit('tree_node_created', {
        node,
        username: username || authenticatedUser.username,
        timestamp: Date.now()
      });
      console.log(`[Workspace] Tree node created in workspace ${workspaceId}: ${node.title} (${node.type})`);
    });

    socket.on('tree_node_renamed', (data) => {
      const { workspaceId, nodeId, newTitle, username } = data;
      if (!workspaceId || !nodeId) return;

      const workspaceRoom = `workspace_${workspaceId}`;
      socket.to(workspaceRoom).emit('tree_node_renamed', {
        nodeId,
        newTitle,
        username: username || authenticatedUser.username,
        timestamp: Date.now()
      });
      console.log(`[Workspace] Tree node renamed in workspace ${workspaceId}: ${nodeId} -> ${newTitle}`);
    });

    socket.on('tree_node_deleted', (data) => {
      const { workspaceId, nodeId, username } = data;
      if (!workspaceId || !nodeId) return;

      const workspaceRoom = `workspace_${workspaceId}`;
      socket.to(workspaceRoom).emit('tree_node_deleted', {
        nodeId,
        username: username || authenticatedUser.username,
        timestamp: Date.now()
      });
      console.log(`[Workspace] Tree node deleted in workspace ${workspaceId}: ${nodeId}`);
    });

    socket.on('tree_node_moved', (data) => {
      const { workspaceId, nodeId, newParentId, newOrderIndex, username } = data;
      if (!workspaceId || !nodeId) return;

      const workspaceRoom = `workspace_${workspaceId}`;
      socket.to(workspaceRoom).emit('tree_node_moved', {
        nodeId,
        newParentId,
        newOrderIndex,
        username: username || authenticatedUser.username,
        timestamp: Date.now()
      });
      console.log(`[Workspace] Tree node moved in workspace ${workspaceId}: ${nodeId} -> parent ${newParentId}`);
    });

    // Handle user color updates (when user changes their color in settings)
    socket.on('update_color', (data) => {
      const { room, color } = data;
      const roomObj = rooms[room];
      if (!roomObj) return;

      const user = roomObj.users[socket.id];
      if (!user) return;

      // Update user's color
      user.color = color;

      // Update cursor color if exists
      if (roomObj.cursors[socket.id]) {
        roomObj.cursors[socket.id].color = color;
      }

      // Broadcast color change to all other users in the room
      socket.to(room).emit('user_color_updated', {
        userId: socket.id,
        username: user.username,
        color: color
      });

      console.log(`[Color] User "${user.username}" updated color to ${color} in room "${room}"`);
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
      const existingTimer = saveTimers.get(room);
      if (existingTimer) {
        clearTimeout(existingTimer);
        saveTimers.delete(room);
      }
      const doc = ydocs.get(room);
      if (doc) {
        // Beispiel: Raum-Name als Prompt-Name speichern
        // Wenn du einen anderen Namen willst, kannst du das anpassen
        await saveYdocToDB(room, doc, `Room ${room}`, null, socket.user?.username || null);
        ydocs.delete(room);
      }
      delete rooms[room];
    }
  }
}

module.exports = setupSocketHandlers;
