// auth.js - JWT Authentication for WebSocket Connections
const jwt = require('jsonwebtoken');
const jwksClient = require('jwks-rsa');

// Keycloak configuration from environment variables
const KEYCLOAK_URL = process.env.KEYCLOAK_URL || 'http://keycloak-service:8080';
const KEYCLOAK_REALM = process.env.KEYCLOAK_REALM || 'llars';

// JWKS client to fetch Keycloak public keys
const client = jwksClient({
  jwksUri: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/certs`,
  cache: true,
  cacheMaxAge: 600000, // 10 minutes
  rateLimit: true,
  jwksRequestsPerMinute: 10
});

/**
 * Get the signing key from Keycloak JWKS endpoint
 */
function getKey(header, callback) {
  client.getSigningKey(header.kid, (err, key) => {
    if (err) {
      console.error('Error fetching signing key:', err);
      return callback(err);
    }
    const signingKey = key.getPublicKey();
    callback(null, signingKey);
  });
}

/**
 * Verify and decode a JWT token
 * @param {string} token - The JWT token to verify
 * @returns {Promise<object>} - The decoded token payload
 */
function verifyToken(token) {
  return new Promise((resolve, reject) => {
    jwt.verify(
      token,
      getKey,
      {
        algorithms: ['RS256'],
        issuer: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}`
      },
      (err, decoded) => {
        if (err) {
          console.error('JWT verification failed:', err.message);
          return reject(err);
        }
        resolve(decoded);
      }
    );
  });
}

/**
 * Extract user information from decoded token
 * @param {object} decodedToken - The decoded JWT payload
 * @returns {object} - User information
 */
function extractUserInfo(decodedToken) {
  return {
    username: decodedToken.preferred_username || decodedToken.sub,
    userId: decodedToken.sub,
    email: decodedToken.email,
    roles: [
      ...(decodedToken.realm_access?.roles || []),
      ...(decodedToken.resource_access?.['llars-backend']?.roles || [])
    ],
    isAdmin: (decodedToken.realm_access?.roles || []).includes('admin')
  };
}

/**
 * Socket.IO middleware for JWT authentication
 * @param {object} socket - The socket.io socket object
 * @param {function} next - The next middleware function
 */
async function authenticateSocket(socket, next) {
  try {
    // Get token from handshake auth or query parameters
    const token = socket.handshake.auth.token || socket.handshake.query.token;

    if (!token) {
      console.warn(`[Auth] Socket ${socket.id} - No token provided`);
      return next(new Error('Authentication required: No token provided'));
    }

    // Verify the JWT token
    const decoded = await verifyToken(token);

    // Attach user information to socket
    socket.user = extractUserInfo(decoded);
    socket.authenticated = true;

    console.log(`[Auth] Socket ${socket.id} - Authenticated as ${socket.user.username}`);
    next();
  } catch (error) {
    console.error(`[Auth] Socket ${socket.id} - Authentication failed:`, error.message);
    next(new Error(`Authentication failed: ${error.message}`));
  }
}

module.exports = {
  authenticateSocket,
  verifyToken,
  extractUserInfo
};
