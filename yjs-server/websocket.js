/**
 * @fileoverview YJS WebSocket Server for Real-time Collaborative Editing
 *
 * This module handles WebSocket connections for the LLARS collaborative editing system.
 * It supports:
 * - Real-time document synchronization via Yjs CRDTs
 * - Multi-user cursor tracking and presence
 * - Debounced persistence to MariaDB
 * - Workspace-level event broadcasting for Git panel updates
 *
 * @module websocket
 * @requires yjs
 * @requires ./db/db
 * @requires ./utils
 *
 * @example
 * // Server setup (server.js)
 * const setupSocketHandlers = require('./websocket');
 * const io = new Server(server);
 * setupSocketHandlers(io);
 */

const Y = require('yjs');
const pool = require('./db/db'); // Verbindung zur Datenbank
const { logRoomsAndUsers, printYDoc } = require('./utils');

/**
 * In-memory cache of Yjs documents.
 * Documents are loaded from DB on first access and persisted on changes.
 * @type {Map<string, Y.Doc>}
 */
const ydocs = new Map();

/**
 * Global Socket.IO instance reference.
 * Stored at module level to enable event emission from async functions
 * like saveYdocToDB, which runs after the debounce timer and needs to
 * broadcast document_saved events to workspace rooms.
 *
 * @type {import('socket.io').Server|null}
 * @see saveYdocToDB - Uses this to emit document_saved events
 */
let ioInstance = null;

/**
 * Room management with extended awareness tracking.
 *
 * Tracks connected users and their cursor positions per room.
 * Room names follow the pattern: `{type}_{id}` where type is 'prompt', 'markdown', or 'latex'.
 *
 * @type {Object.<string, {users: Object, cursors: Object}>}
 * @property {Object.<string, {username: string, color: string, userId: number, isAdmin: boolean}>} users - Connected users by socket ID
 * @property {Object.<string, {blockId: string, range: Object, username: string, color: string}>} cursors - Cursor positions by socket ID
 *
 * @example
 * // Room structure
 * rooms['latex_42'] = {
 *   users: { 'socket123': { username: 'alice', color: '#FF6B6B', userId: 1, isAdmin: false } },
 *   cursors: { 'socket123': { blockId: 'block-1', range: { index: 10, length: 5 }, ... } }
 * }
 */
const rooms = {};

/**
 * Debounce timers for persisting documents to DB.
 * Each room has at most one pending save timer.
 * After 2 seconds of inactivity, the document is persisted.
 * @type {Map<string, NodeJS.Timeout>}
 */
const saveTimers = new Map();

/**
 * Color palette for user cursor/presence indicators.
 * Colors are chosen to be visually distinct and accessible.
 * @constant {string[]}
 */
const COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
  '#FFEEAD', '#D4A5A5', '#9B59B6', '#3498DB'
];

/**
 * Get a random color from the palette.
 * Used when user doesn't have a persisted collab_color preference.
 * @returns {string} Hex color code
 */
function getRandomColor() {
  return COLORS[Math.floor(Math.random() * COLORS.length)];
}

/**
 * Serialize a Yjs document to JSON string for database storage.
 * Converts the binary state update to a JSON array of numbers.
 *
 * @param {Y.Doc} doc - The Yjs document to serialize
 * @returns {string} JSON string representation of the document state
 */
function ydocToJson(doc) {
  const update = Y.encodeStateAsUpdate(doc);
  return JSON.stringify(Array.from(update));
}

/**
 * Deserialize a JSON string back to a Yjs document.
 *
 * @param {string} jsonString - JSON string from ydocToJson
 * @returns {Y.Doc} Reconstructed Yjs document
 * @throws {Error} If JSON is malformed
 */
function jsonToYdoc(jsonString) {
  const update = new Uint8Array(JSON.parse(jsonString));
  const doc = new Y.Doc();
  Y.applyUpdate(doc, update);
  return doc;
}

/**
 * Parse a room name to extract document type and ID.
 *
 * Room naming convention:
 * - `room_{id}` - Prompt Engineering documents
 * - `markdown_{id}` - Markdown Collab documents
 * - `latex_{id}` - LaTeX Collab documents
 *
 * @param {string} roomName - The room name to parse
 * @returns {{kind: 'prompt'|'markdown'|'latex', id: number}|null} Parsed info or null if invalid
 *
 * @example
 * parseRoom('latex_42') // { kind: 'latex', id: 42 }
 * parseRoom('invalid')  // null
 */
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

/**
 * Check if a user has access to a Markdown document.
 * Access is granted if user is admin, workspace owner, or workspace member.
 *
 * @param {number} documentId - The markdown document ID
 * @param {string} username - Username to check access for
 * @param {boolean} isAdmin - Whether the user has admin privileges
 * @returns {Promise<boolean>} True if user has access
 */
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

/**
 * Check if a user has access to a LaTeX document.
 * Access is granted if user is admin, workspace owner, or workspace member.
 *
 * @param {number} documentId - The latex document ID
 * @param {string} username - Username to check access for
 * @param {boolean} isAdmin - Whether the user has admin privileges
 * @returns {Promise<boolean>} True if user has access
 */
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
 * Persist a Yjs document to the database.
 *
 * This function handles saving for all document types (prompt, markdown, latex).
 * For markdown and latex documents, it also emits a `document_saved` event
 * to the workspace room, enabling real-time Git panel updates.
 *
 * Storage format:
 * - `content`: JSON-serialized Yjs state (full CRDT history)
 * - `content_text`: Plain text extraction for Git diff, search, and fallback loading
 *
 * Event emission (for markdown/latex):
 * - Event: `document_saved`
 * - Room: `workspace_{type}_{workspaceId}` (e.g., `workspace_latex_42`)
 * - Payload: `{ documentId, workspaceId, kind, contentLength, savedAt }`
 *
 * @param {string} roomName - Room name in format `{type}_{id}` (e.g., 'latex_42')
 * @param {Y.Doc} doc - The Yjs document to persist
 * @param {string} name - Document name (used for prompts only)
 * @param {number|null} userId - Owner user ID (can be null)
 * @param {string|null} username - Username for last_editor tracking (optional)
 *
 * @fires document_saved - Broadcast to workspace room for real-time Git updates
 *
 * @example
 * // Called after debounce timer expires
 * await saveYdocToDB('latex_42', doc, 'Room latex_42', userId, 'alice')
 * // Emits to 'workspace_latex_5' if doc belongs to workspace 5
 */
/**
 * Extract rendered blocks from a Yjs document with {{variable}} placeholders as text.
 *
 * Yjs stores Quill embeds (VariableBlot) as embedded objects in Y.Text deltas.
 * Python's y-py library loses these embeds when converting to string.
 * This function reads the delta ops and converts {variable: "name"} → {{name}}.
 *
 * @param {Y.Doc} doc - The Yjs document
 * @returns {Object|null} - {blocks: {blockId: {title, position, content}}} or null
 */
function extractRenderedBlocks(doc) {
  const blocksMap = doc.getMap('blocks');
  if (!blocksMap || blocksMap.size === 0) return null;

  const result = {};
  blocksMap.forEach((blockValue, blockId) => {
    if (!blockValue || typeof blockValue.get !== 'function') return;
    const title = blockValue.get('title') || blockId;
    const position = blockValue.get('position') || 0;
    const ytext = blockValue.get('content');

    let textContent = '';
    if (ytext && typeof ytext.toDelta === 'function') {
      for (const op of ytext.toDelta()) {
        if (typeof op.insert === 'string') {
          textContent += op.insert;
        } else if (op.insert && typeof op.insert === 'object') {
          if (op.insert.variable) {
            textContent += `{{${op.insert.variable}}}`;
          }
        }
      }
    } else if (ytext) {
      textContent = ytext.toString();
    }

    result[blockId] = { title, position, content: textContent };
  });
  return { blocks: result };
}

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

  // DEBUG: Log what we're about to save
  console.log(`[saveYdocToDB] Room: ${roomName}, docId: ${roomId}, contentLength: ${textContent.length}, preview: "${textContent.substring(0, 100)}..."`);

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

      // Extract rendered content with {{variables}} as text for reliable generation
      const rendered = extractRenderedBlocks(doc);
      if (rendered) {
        await pool.query(
          'UPDATE user_prompts SET rendered_content = ? WHERE prompt_id = ?',
          [JSON.stringify(rendered), roomId]
        );
      }

      console.log(`Y.Doc für Raum ${roomName} (prompt_id=${roomId}) gespeichert.`);
      return;
    }

    if (parsed.kind === 'markdown') {
      const [rows] = await pool.query(
        'SELECT id, workspace_id FROM markdown_documents WHERE id = ?',
        [roomId]
      );

      if (rows.length === 0) {
        console.warn(`Markdown document ${roomId} not found; cannot persist Y.Doc for room ${roomName}`);
        return;
      }

      await pool.query(
        `UPDATE markdown_documents
         SET content = ?, content_text = ?, updated_at = NOW(), last_editor_username = COALESCE(?, last_editor_username)
         WHERE id = ?`,
        [jsonString, textContent, username, roomId]
      );
      console.log(`Y.Doc für Raum ${roomName} (markdown_documents.id=${roomId}) gespeichert.`);

      // =====================================================================
      // Real-time Git Panel Update: Emit document_saved to workspace room
      // =====================================================================
      // After persisting to DB, broadcast to all clients in the workspace.
      // This enables the Git panel to refresh and show uncommitted changes
      // in real-time without polling. The event is sent to a workspace-level
      // room (not document room) so ALL users editing ANY document in the
      // workspace receive the notification and can refresh their Git panels.
      // =====================================================================
      if (ioInstance && rows[0].workspace_id) {
        const workspaceId = rows[0].workspace_id;
        const workspaceRoom = `workspace_markdown_${workspaceId}`;
        ioInstance.to(workspaceRoom).emit('document_saved', {
          documentId: roomId,
          workspaceId: workspaceId,
          kind: 'markdown',
          contentLength: textContent.length,
          savedAt: new Date().toISOString()
        });
        console.log(`[document_saved] Emitted to ${workspaceRoom} for markdown doc ${roomId}`);
      }
    }

    if (parsed.kind === 'latex') {
      const [rows] = await pool.query(
        'SELECT id, workspace_id FROM latex_documents WHERE id = ?',
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

      // =====================================================================
      // Real-time Git Panel Update: Emit document_saved to workspace room
      // =====================================================================
      // Same as markdown above - broadcast save event for Git panel refresh.
      // See markdown section for detailed explanation of the architecture.
      // =====================================================================
      if (ioInstance && rows[0].workspace_id) {
        const workspaceId = rows[0].workspace_id;
        const workspaceRoom = `workspace_latex_${workspaceId}`;
        ioInstance.to(workspaceRoom).emit('document_saved', {
          documentId: roomId,
          workspaceId: workspaceId,
          kind: 'latex',
          contentLength: textContent.length,
          savedAt: new Date().toISOString()
        });
        console.log(`[document_saved] Emitted to ${workspaceRoom} for latex doc ${roomId}`);
      }
    }
  } catch (err) {
    console.error(`Fehler beim Speichern des Y.Doc für Raum ${roomName}:`, err);
  }
}

/**
 * Load a Yjs document from the database.
 *
 * Loading strategy with fallback:
 * 1. Try to load from `content` column (JSON-serialized Yjs state)
 * 2. If `content` is corrupt/empty, fall back to `content_text` (plain text)
 * 3. If neither exists, return empty Y.Doc
 *
 * The fallback to content_text ensures documents remain accessible even if
 * the Yjs CRDT state becomes corrupt. This is especially important for
 * documents created before Yjs integration or after manual DB edits.
 *
 * @param {string} roomName - Room name in format `{type}_{id}` (e.g., 'latex_42')
 * @returns {Promise<Y.Doc>} Loaded Yjs document (or empty doc if not found)
 */
async function loadYdocFromDB(roomName) {
  console.log(`[loadYdocFromDB] Loading room: ${roomName}`);
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
        // Check if content is YJS binary format (JSON array) or plain JSON (object with blocks)
        let contentData;
        try {
          contentData = typeof rows[0].content === 'string'
            ? JSON.parse(rows[0].content)
            : rows[0].content;
        } catch (e) {
          console.error(`[loadYdocFromDB] Failed to parse prompt content for ${roomId}:`, e.message);
          return new Y.Doc();
        }

        // If it's a plain JSON object with blocks structure (from seeder), convert to YJS
        if (contentData && typeof contentData === 'object' && contentData.blocks && !Array.isArray(contentData)) {
          console.log(`[loadYdocFromDB] Converting plain JSON prompt ${roomId} to YJS format`);
          const doc = new Y.Doc();
          const blocksMap = doc.getMap('blocks');

          // Convert each block to YJS structure
          for (const [blockId, blockData] of Object.entries(contentData.blocks)) {
            const blockMap = new Y.Map();
            blockMap.set('title', blockData.title || blockId);
            blockMap.set('position', blockData.position || 0);

            // Content must be Y.Text for collaborative editing
            const ytext = new Y.Text();
            if (blockData.content) {
              ytext.insert(0, blockData.content);
            }
            blockMap.set('content', ytext);

            blocksMap.set(blockId, blockMap);
          }

          // Save the converted YJS state back to DB for future loads
          const jsonString = ydocToJson(doc);
          pool.query(
            'UPDATE user_prompts SET content = ?, updated_at = NOW() WHERE prompt_id = ?',
            [jsonString, roomId]
          ).catch(e => console.error(`[loadYdocFromDB] Failed to save converted prompt ${roomId}:`, e.message));

          return doc;
        }

        // It's already YJS binary format (array of numbers)
        if (Array.isArray(contentData)) {
          return jsonToYdoc(rows[0].content);
        }

        console.warn(`[loadYdocFromDB] Unknown content format for prompt ${roomId}`);
        return new Y.Doc();
      }
      return new Y.Doc();
    }

    if (parsed.kind === 'markdown') {
      const [rows] = await pool.query(
        'SELECT content FROM markdown_documents WHERE id = ?',
        [roomId]
      );
      if (rows.length > 0 && rows[0].content) {
        try {
          return jsonToYdoc(rows[0].content);
        } catch (e) {
          console.error(`[loadYdocFromDB] Failed to parse YJS JSON for markdown doc ${roomId}:`, e.message);
          // Return empty doc - markdown has no content_text fallback
          return new Y.Doc();
        }
      }
      return new Y.Doc();
    }

    if (parsed.kind === 'latex') {
      const [rows] = await pool.query(
        'SELECT content, content_text FROM latex_documents WHERE id = ?',
        [roomId]
      );
      if (rows.length > 0) {
        const hasContent = !!rows[0].content;
        const hasContentText = !!rows[0].content_text;
        const contentTextLength = rows[0].content_text ? rows[0].content_text.length : 0;
        console.log(`[loadYdocFromDB] Latex doc ${roomId}: hasContent=${hasContent}, hasContentText=${hasContentText}, contentTextLength=${contentTextLength}`);

        // Try to load from YJS JSON content first
        if (rows[0].content) {
          try {
            console.log(`[loadYdocFromDB] Trying YJS JSON content for doc ${roomId}`);
            const doc = jsonToYdoc(rows[0].content);
            // Verify the doc has content (not a corrupt/empty state)
            const text = doc.getText('content').toString();
            if (text.length > 0 || !rows[0].content_text) {
              console.log(`[loadYdocFromDB] Using YJS JSON content for doc ${roomId}, text length: ${text.length}`);
              return doc;
            }
            // YJS content is empty but content_text exists - fall through to use content_text
            console.log(`[loadYdocFromDB] YJS JSON content is empty, falling back to content_text for doc ${roomId}`);
          } catch (e) {
            console.error(`[loadYdocFromDB] Failed to parse YJS JSON for doc ${roomId}, falling back to content_text:`, e.message);
            // Fall through to content_text fallback
          }
        }

        // Fallback: use content_text
        if (rows[0].content_text) {
          console.log(`[loadYdocFromDB] Using content_text for doc ${roomId}: "${rows[0].content_text.substring(0, 100)}..."`);
          const doc = new Y.Doc();
          doc.getText('content').insert(0, rows[0].content_text);
          return doc;
        }
      }
      console.log(`[loadYdocFromDB] No content found for doc ${roomId}, returning empty doc`);
      return new Y.Doc();
    }
  } catch (err) {
    console.error(`Fehler beim Laden des Y.Doc für Raum ${roomName}:`, err);
  }
  return new Y.Doc();
}

/**
 * Get or create a room object for tracking users and cursors.
 *
 * @param {string} roomName - The room name
 * @returns {{users: Object, cursors: Object}} Room object
 */
function getOrCreateRoom(roomName) {
  if (!rooms[roomName]) {
    rooms[roomName] = {
      users: {},    // socketId -> { username, color }
      cursors: {},  // socketId -> { blockId, range, username, color }
      workspaceId: null,  // Cached workspace ID for real-time updates
      kind: null    // Document kind (latex, markdown, prompt)
    };
  }
  return rooms[roomName];
}

/**
 * Set up all Socket.IO event handlers for collaborative editing.
 *
 * This is the main entry point for the WebSocket server. It handles:
 * - Authentication (via middleware in server.js)
 * - Room management (join/leave)
 * - Yjs document synchronization
 * - Cursor/presence tracking
 * - Workspace tree updates
 * - Real-time Git panel notifications
 *
 * Room Types:
 * - Document rooms: `{type}_{id}` - For Yjs sync and cursors
 * - Workspace rooms: `workspace_{type}_{id}` - For document_saved events
 *
 * @param {import('socket.io').Server} io - Socket.IO server instance
 *
 * @example
 * // In server.js
 * const io = new Server(server);
 * setupSocketHandlers(io);
 */
function setupSocketHandlers(io) {
  // Store io instance at module level for use in async functions.
  // This is necessary because saveYdocToDB runs after a debounce timer
  // and needs to emit events, but doesn't have direct access to io.
  ioInstance = io;

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

      // Join the document room for Yjs sync and cursor updates
      socket.join(room);

      // =====================================================================
      // Workspace Room Subscription for Real-time Git Panel Updates
      // =====================================================================
      // In addition to the document room, join the workspace-level room.
      // This is essential for receiving `document_saved` events that trigger
      // Git panel refreshes. The workspace room pattern is:
      //   `workspace_{type}_{workspaceId}` (e.g., 'workspace_latex_42')
      //
      // Why workspace-level rooms?
      // - Document rooms only contain users editing THAT specific document
      // - Git panel needs updates when ANY document in the workspace changes
      // - Broadcasting to workspace room ensures all workspace users see updates
      //
      // We also cache workspaceId in the room object to avoid DB queries on
      // every sync_update when emitting document_updated events.
      // =====================================================================
      const roomObj = getOrCreateRoom(room);
      roomObj.kind = parsed?.kind || null;

      if (parsed?.kind === 'latex') {
        const [wsRows] = await pool.query(
          'SELECT workspace_id FROM latex_documents WHERE id = ?',
          [parsed.id]
        );
        if (wsRows.length > 0 && wsRows[0].workspace_id) {
          roomObj.workspaceId = wsRows[0].workspace_id;
          const workspaceRoom = `workspace_latex_${wsRows[0].workspace_id}`;
          socket.join(workspaceRoom);
          console.log(`[join_room] Also joined workspace room: ${workspaceRoom}`);
        }

        // Load baseline will happen after doc is loaded (see below)
      } else if (parsed?.kind === 'markdown') {
        const [wsRows] = await pool.query(
          'SELECT workspace_id FROM markdown_documents WHERE id = ?',
          [parsed.id]
        );
        if (wsRows.length > 0 && wsRows[0].workspace_id) {
          roomObj.workspaceId = wsRows[0].workspace_id;
          const workspaceRoom = `workspace_markdown_${wsRows[0].workspace_id}`;
          socket.join(workspaceRoom);
          console.log(`[join_room] Also joined workspace room: ${workspaceRoom}`);
        }

        // Load baseline will happen after doc is loaded (see below)
      }

      let doc = ydocs.get(room);

      // Lade Y.Doc aus der Datenbank, wenn es noch nicht im Speicher ist
      if (!doc) {
        doc = await loadYdocFromDB(room);
        ydocs.set(room, doc);
      }

      // =====================================================================
      // Store baseline in YJS Map for client-side diff calculation
      // =====================================================================
      // The baseline (last committed content) is stored in the YJS document
      // itself, so all clients can calculate diffs locally without server
      // roundtrips. This enables truly instant diff updates.
      // =====================================================================
      const baselineMap = doc.getMap('baseline');
      if (!baselineMap.has('text')) {
        // Load baseline from DB (last commit snapshot)
        let baseline = '';
        if (parsed?.kind === 'latex') {
          const [commitRows] = await pool.query(
            `SELECT content_snapshot FROM latex_commits
             WHERE document_id = ? AND content_snapshot IS NOT NULL
             ORDER BY created_at DESC, id DESC LIMIT 1`,
            [parsed.id]
          );
          baseline = commitRows.length > 0 ? (commitRows[0].content_snapshot || '') : '';
        } else if (parsed?.kind === 'markdown') {
          const [commitRows] = await pool.query(
            `SELECT content_snapshot FROM markdown_commits
             WHERE document_id = ? AND content_snapshot IS NOT NULL
             ORDER BY created_at DESC, id DESC LIMIT 1`,
            [parsed.id]
          );
          baseline = commitRows.length > 0 ? (commitRows[0].content_snapshot || '') : '';
        }
        baselineMap.set('text', baseline);
        console.log(`[join_room] Stored baseline in YJS Map for ${room}: ${baseline.length} chars`);
      }

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

    socket.on('sync_update', async (data) => {
      const { room, update } = data;
      const doc = ydocs.get(room);
      if (!doc) {
        console.warn(`[sync_update] No doc found for room "${room}", ignoring update`);
        return;
      }
      try {
        const uint8Update = new Uint8Array(update);
        Y.applyUpdate(doc, uint8Update);
        // Optional: Debug-Ausgabe
        printYDoc(doc);

        // Weiterleiten an alle anderen Clients im Raum
        socket.to(room).emit('sync_update', { update });

        // =====================================================================
        // Real-time Git Panel Update: Emit document_updated IMMEDIATELY
        // =====================================================================
        // Unlike document_saved (which fires after 2s debounce), this event
        // fires on EVERY sync_update. Clients calculate diff locally using
        // the baseline stored in the YJS document for truly instant updates.
        // =====================================================================
        const roomObj = rooms[room];
        if (roomObj && roomObj.workspaceId && roomObj.kind) {
          const workspaceRoom = `workspace_${roomObj.kind}_${roomObj.workspaceId}`;
          const parsed = parseRoom(room);

          // Emit lightweight event - clients calculate diff locally
          ioInstance.to(workspaceRoom).emit('document_updated', {
            documentId: parsed?.id || null,
            workspaceId: roomObj.workspaceId,
            kind: roomObj.kind,
            timestamp: Date.now()
          });
        }

        // Debounced persistence to reduce data-loss on server restarts.
        const existingTimer = saveTimers.get(room);
        if (existingTimer) clearTimeout(existingTimer);
        console.log(`[sync_update] Setting debounced save timer for room "${room}"`);
        saveTimers.set(room, setTimeout(async () => {
          console.log(`[sync_update] Debounced save timer fired for room "${room}"`);
          try {
            await saveYdocToDB(room, doc, `Room ${room}`, authenticatedUser.userId || null, authenticatedUser.username || null);
          } catch (e) {
            console.error(`Debounced save failed for room ${room}:`, e);
          } finally {
            saveTimers.delete(room);
          }
        }, 2000));  // 2s debounce for DB writes (Git panel uses real-time diff from document_updated)
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

    /**
     * Reload document from database and broadcast to all clients.
     * Used after rollback/revert operations to sync editor with DB state.
     */
    socket.on('reload_room', async (data, callback) => {
      const room = data?.room;
      if (!room) {
        if (callback) callback({ success: false, error: 'room is required' });
        return;
      }

      console.log(`[reload_room] START - Reloading room "${room}" from database (requested by ${authenticatedUser.username})`);

      // Cancel any pending save to prevent overwriting the DB with stale data
      const existingTimer = saveTimers.get(room);
      if (existingTimer) {
        console.log(`[reload_room] Cancelled pending save timer for room "${room}"`);
        clearTimeout(existingTimer);
        saveTimers.delete(room);
      }

      try {
        // Log current cached doc state before removing
        const oldDoc = ydocs.get(room);
        if (oldDoc) {
          const oldContent = oldDoc.getText('content').toString();
          console.log(`[reload_room] Old cached doc content length: ${oldContent.length}, preview: "${oldContent.substring(0, 100)}..."`);
        } else {
          console.log(`[reload_room] No cached doc found for room "${room}"`);
        }

        // Remove the cached doc to force reload from DB
        ydocs.delete(room);

        // Load fresh content from database
        const doc = await loadYdocFromDB(room);
        ydocs.set(room, doc);

        // Log new content
        const newContent = doc.getText('content').toString();
        console.log(`[reload_room] New doc content length: ${newContent.length}, preview: "${newContent.substring(0, 100)}..."`);

        // =====================================================================
        // Update baseline in YJS Map for correct diff calculation after revert.
        // After a revert, the baseline IS the current content (no uncommitted changes).
        // =====================================================================
        const parsed = parseRoom(room);
        if (parsed?.kind === 'latex' || parsed?.kind === 'markdown') {
          const baselineMap = doc.getMap('baseline');
          baselineMap.set('text', newContent);
          console.log(`[reload_room] Updated baseline in YJS Map: ${newContent.length} chars`);
        }

        // =====================================================================
        // FORCE RELOAD: Send special event that tells ALL clients to recreate
        // their local ydoc. This is necessary because Y.applyUpdate() MERGES
        // updates instead of replacing them, which would cause content duplication.
        //
        // The force_reload event contains the full snapshot. Clients must:
        // 1. Destroy their existing ydoc
        // 2. Create a fresh ydoc
        // 3. Apply this snapshot to the fresh ydoc
        // =====================================================================
        const fullState = Y.encodeStateAsUpdate(doc);
        io.to(room).emit('force_reload', {
          room,
          snapshot: Array.from(fullState)
        });

        console.log(`[reload_room] END - Room "${room}" reloaded, force_reload sent to all clients`);
        if (callback) callback({ success: true });
      } catch (e) {
        console.error(`[reload_room] FAILED for room ${room}:`, e);
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

/**
 * Handle user leaving a room (disconnect or explicit leave).
 *
 * Cleanup actions:
 * 1. Remove user from room's users and cursors tracking
 * 2. Notify other users in the room about the departure
 * 3. If room is empty: save document to DB and clean up memory
 *
 * @param {import('socket.io').Socket} socket - The disconnecting socket
 * @param {string} room - Room name to leave
 */
async function handleUserLeave(socket, room) {
  console.log(`[handleUserLeave] User leaving room "${room}"`);
  socket.leave(room);
  const roomObj = rooms[room];

  if (roomObj) {
    delete roomObj.users[socket.id];
    delete roomObj.cursors[socket.id];

    // Informiere andere Benutzer
    socket.to(room).emit('user_left', { userId: socket.id });

    // Räume den Raum auf, wenn er leer ist
    const remainingUsers = Object.keys(roomObj.users).length;
    console.log(`[handleUserLeave] Remaining users in room "${room}": ${remainingUsers}`);

    if (remainingUsers === 0) {
      const existingTimer = saveTimers.get(room);
      if (existingTimer) {
        console.log(`[handleUserLeave] Cancelling pending save timer for room "${room}"`);
        clearTimeout(existingTimer);
        saveTimers.delete(room);
      }
      const doc = ydocs.get(room);
      if (doc) {
        const content = doc.getText('content').toString();
        console.log(`[handleUserLeave] Saving doc for empty room "${room}", content length: ${content.length}`);
        await saveYdocToDB(room, doc, `Room ${room}`, null, socket.user?.username || null);
        ydocs.delete(room);
      }
      delete rooms[room];
      console.log(`[handleUserLeave] Room "${room}" cleaned up`);
    }
  }
}

module.exports = setupSocketHandlers;
