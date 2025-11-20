# YJS Server - Real-time Collaboration with Keycloak Authentication

This is a WebSocket server for real-time collaborative editing using YJS (Yjs CRDT library) and Socket.IO, secured with Keycloak JWT authentication.

## Features

- **Real-time Collaboration**: Multiple users can edit documents simultaneously
- **JWT Authentication**: All WebSocket connections are secured with Keycloak tokens
- **User Tracking**: Track active users and their cursors in real-time
- **Database Persistence**: Documents are automatically saved to MySQL database
- **Awareness**: See other users' cursors and presence

## Authentication Flow

### 1. Client Connection
The client must provide a valid Keycloak JWT token when connecting to the WebSocket:

```javascript
const socket = io('http://localhost:8082', {
  path: '/collab/socket.io/',
  auth: {
    token: keycloakToken  // Get this from Keycloak after login
  }
});
```

### 2. Token Validation
The server automatically validates the token using the `authenticateSocket` middleware:
- Fetches Keycloak public keys from JWKS endpoint
- Verifies JWT signature with RS256 algorithm
- Checks token expiration and issuer
- Extracts user information (username, userId, roles)

### 3. Authenticated Connection
If valid, the socket receives authenticated user information:
```javascript
socket.user = {
  username: 'john.doe',
  userId: 'uuid-here',
  email: 'john@example.com',
  roles: ['rater', 'viewer'],
  isAdmin: false
}
```

## Event API

### Client → Server Events

#### `join_room`
Join a collaborative editing room.

**Payload:**
```javascript
{
  room: 'room_123'  // Only room ID needed, user info comes from token!
}
```

**Response:**
- `snapshot_document`: Full document state
- `room_state`: Current users and cursors
- Broadcasts `user_joined` to other clients

#### `sync_update`
Send document changes to other clients.

**Payload:**
```javascript
{
  room: 'room_123',
  update: Uint8Array  // Y.js update
}
```

#### `cursor_update`
Update cursor position.

**Payload:**
```javascript
{
  room: 'room_123',
  blockId: 'block-uuid',
  range: { index: 0, length: 0 } // or null to hide cursor
}
```

#### `leave_room`
Leave a room.

**Payload:**
```javascript
'room_123'
```

### Server → Client Events

#### `snapshot_document`
Sent when joining a room, contains the full document state.

**Payload:** `Uint8Array` (Y.js state)

#### `room_state`
Current state of the room (users and cursors).

**Payload:**
```javascript
{
  users: {
    'socket-id-1': { username: 'john', userId: 'uuid', color: '#FF6B6B', isAdmin: false }
  },
  cursors: {
    'socket-id-1': { blockId: 'block-1', range: {...}, username: 'john', color: '#FF6B6B' }
  }
}
```

#### `user_joined`
Broadcast when a new user joins.

**Payload:**
```javascript
{
  userId: 'socket-id',
  username: 'john',
  color: '#FF6B6B'
}
```

#### `user_left`
Broadcast when a user leaves.

**Payload:**
```javascript
{
  userId: 'socket-id'
}
```

#### `sync_update`
Broadcast Y.js document updates.

**Payload:**
```javascript
{
  update: Uint8Array
}
```

#### `cursor_updated`
Broadcast cursor position changes.

**Payload:**
```javascript
{
  userId: 'socket-id',
  cursor: { blockId: 'block-1', range: {...}, username: 'john', color: '#FF6B6B' }
}
```

## Security Features

### Authentication
- **Mandatory JWT**: All connections require valid Keycloak token
- **Token Expiration**: Expired tokens are rejected
- **Signature Verification**: Tokens are verified with Keycloak public keys
- **User Spoofing Prevention**: Username/userId cannot be spoofed by client

### Authorization (Future Enhancement)
- Room-level permissions based on Keycloak roles
- Admin-only document deletion
- Read-only mode for viewers

## Environment Variables

```bash
KEYCLOAK_URL=http://keycloak-service:8080  # Keycloak server URL
KEYCLOAK_REALM=llars                       # Keycloak realm name
PORT=8082                                   # Server port
MYSQL_HOST=db-maria-service                # Database host
MYSQL_PORT=3306                            # Database port
MYSQL_USER=user_feature                    # Database user
MYSQL_PASSWORD=password_feature            # Database password
MYSQL_DATABASE=database_llars              # Database name
```

## Installation

```bash
npm install
```

## Running

**Development:**
```bash
npm run dev  # Uses nodemon for auto-reload
```

**Production:**
```bash
npm start
```

## Database Schema

The server expects a `user_prompts` table:

```sql
CREATE TABLE user_prompts (
  prompt_id INT PRIMARY KEY,
  user_id VARCHAR(255),
  name VARCHAR(255),
  content TEXT,  -- Y.js document state as JSON
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

## Error Handling

### Connection Errors
- **No token**: `Authentication required: No token provided`
- **Invalid token**: `Authentication failed: jwt malformed`
- **Expired token**: `Authentication failed: jwt expired`
- **Invalid signature**: `Authentication failed: invalid signature`

## Architecture

```
┌─────────────┐         WebSocket + JWT        ┌──────────────┐
│   Client    │ ──────────────────────────────> │  YJS Server  │
│  (Browser)  │ <────────────────────────────── │  (Node.js)   │
└─────────────┘    Real-time collaboration     └──────────────┘
                                                       │
                                                       │ Persist
                                                       ▼
                                                ┌──────────────┐
                                                │    MySQL     │
                                                │   Database   │
                                                └──────────────┘
```

## Testing with curl (WebSocket)

You can test authentication with wscat:

```bash
# Install wscat
npm install -g wscat

# Connect with token
wscat -c "ws://localhost:8082/collab/socket.io/?token=YOUR_JWT_TOKEN"
```

## Production Deployment

### HTTPS/WSS
In production, use nginx to proxy WebSocket connections with SSL:

```nginx
location /collab/ {
    proxy_pass http://yjs-service:8082;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Token Refresh
Frontend should refresh tokens before they expire to maintain connection.

## Troubleshooting

### "Authentication required: No token provided"
- Check that the client is sending the token in `auth: { token: '...' }`
- Verify token is not empty or undefined

### "Authentication failed: jwt expired"
- Token has expired
- Frontend needs to refresh the token using Keycloak

### "Error fetching signing key"
- Keycloak URL is incorrect
- Keycloak is not reachable from the YJS server
- Realm name is incorrect

### Connection refused
- Check that YJS server is running on correct port
- Verify firewall/network configuration
- Check nginx proxy configuration

## References

- [Y.js Documentation](https://docs.yjs.dev/)
- [Socket.IO Documentation](https://socket.io/docs/v4/)
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [jsonwebtoken npm](https://www.npmjs.com/package/jsonwebtoken)
