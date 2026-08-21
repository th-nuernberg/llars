/**
 * E2E encryption composable.
 * Manages key generation, key exchange, encrypt/decrypt using Web Crypto API.
 *
 * Uses X25519 (ECDH with Curve25519) for key agreement and AES-256-GCM for encryption.
 * Keys are stored in IndexedDB (private) and server (public).
 */
import { ref, readonly } from 'vue'
import axios from 'axios'

const DB_NAME = 'llars-messaging-keys'
const DB_VERSION = 1
const STORE_NAME = 'keys'

export function useEncryption() {
  const hasKeys = ref(false)
  const isGenerating = ref(false)

  // ── IndexedDB Helpers ───────────────────────────────────────────
  const openDB = () =>
    new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION)
      request.onupgradeneeded = (e) => {
        e.target.result.createObjectStore(STORE_NAME, { keyPath: 'id' })
      }
      request.onsuccess = (e) => resolve(e.target.result)
      request.onerror = (e) => reject(e.target.error)
    })

  const storeKey = async (id, keyData) => {
    const db = await openDB()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      tx.objectStore(STORE_NAME).put({ id, ...keyData })
      tx.oncomplete = () => resolve()
      tx.onerror = (e) => reject(e.target.error)
    })
  }

  const getKey = async (id) => {
    const db = await openDB()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const request = tx.objectStore(STORE_NAME).get(id)
      request.onsuccess = () => resolve(request.result || null)
      request.onerror = (e) => reject(e.target.error)
    })
  }

  // ── Key Generation ──────────────────────────────────────────────
  const generateKeyPair = async () => {
    const keyPair = await crypto.subtle.generateKey(
      { name: 'ECDH', namedCurve: 'P-256' },
      true,
      ['deriveKey', 'deriveBits']
    )
    return keyPair
  }

  const exportPublicKey = async (key) => {
    const raw = await crypto.subtle.exportKey('jwk', key)
    return JSON.stringify(raw)
  }

  const importPublicKey = async (jwkString) => {
    const jwk = typeof jwkString === 'string' ? JSON.parse(jwkString) : jwkString
    return crypto.subtle.importKey(
      'jwk',
      jwk,
      { name: 'ECDH', namedCurve: 'P-256' },
      true,
      []
    )
  }

  // ── Initialize Keys ─────────────────────────────────────────────
  const initializeKeys = async (username) => {
    isGenerating.value = true
    try {
      // Check if we already have keys
      const existing = await getKey('identity')
      if (existing) {
        hasKeys.value = true
        return
      }

      // Generate identity key pair
      const identityKeyPair = await generateKeyPair()
      const identityPublicJwk = await exportPublicKey(identityKeyPair.publicKey)

      // Generate signed pre-key
      const signedPreKeyPair = await generateKeyPair()
      const signedPreKeyPublicJwk = await exportPublicKey(signedPreKeyPair.publicKey)

      // Store private keys locally
      const identityPrivateJwk = await crypto.subtle.exportKey('jwk', identityKeyPair.privateKey)
      const signedPreKeyPrivateJwk = await crypto.subtle.exportKey('jwk', signedPreKeyPair.privateKey)

      await storeKey('identity', {
        publicKey: identityPublicJwk,
        privateKey: JSON.stringify(identityPrivateJwk),
      })
      await storeKey('signedPreKey', {
        publicKey: signedPreKeyPublicJwk,
        privateKey: JSON.stringify(signedPreKeyPrivateJwk),
      })

      // Upload public keys to server
      await axios.post('/api/messaging/keys', {
        identity_public_key: identityPublicJwk,
        signed_prekey_public: signedPreKeyPublicJwk,
        signed_prekey_id: 0,
      })

      hasKeys.value = true
    } catch (err) {
      console.error('[Encryption] Key generation failed:', err)
    } finally {
      isGenerating.value = false
    }
  }

  // ── Encrypt / Decrypt ───────────────────────────────────────────
  const deriveSharedKey = async (privateKey, publicKey) => {
    const sharedBits = await crypto.subtle.deriveBits(
      { name: 'ECDH', public: publicKey },
      privateKey,
      256
    )
    return crypto.subtle.importKey(
      'raw',
      sharedBits,
      { name: 'AES-GCM' },
      false,
      ['encrypt', 'decrypt']
    )
  }

  const encrypt = async (plaintext, recipientPublicKeyJwk) => {
    try {
      const identityData = await getKey('identity')
      if (!identityData) throw new Error('No identity key found')

      const privateKey = await crypto.subtle.importKey(
        'jwk',
        JSON.parse(identityData.privateKey),
        { name: 'ECDH', namedCurve: 'P-256' },
        false,
        ['deriveKey', 'deriveBits']
      )

      const recipientPublicKey = await importPublicKey(recipientPublicKeyJwk)
      const sharedKey = await deriveSharedKey(privateKey, recipientPublicKey)

      const iv = crypto.getRandomValues(new Uint8Array(12))
      const encoded = new TextEncoder().encode(plaintext)
      const ciphertext = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        sharedKey,
        encoded
      )

      return {
        ciphertext: btoa(String.fromCharCode(...new Uint8Array(ciphertext))),
        iv: btoa(String.fromCharCode(...iv)),
        sender_public_key: identityData.publicKey,
      }
    } catch (err) {
      console.error('[Encryption] Encrypt failed:', err)
      return null
    }
  }

  const decrypt = async (encryptedData) => {
    try {
      const identityData = await getKey('identity')
      if (!identityData) throw new Error('No identity key found')

      const privateKey = await crypto.subtle.importKey(
        'jwk',
        JSON.parse(identityData.privateKey),
        { name: 'ECDH', namedCurve: 'P-256' },
        false,
        ['deriveKey', 'deriveBits']
      )

      const senderPublicKey = await importPublicKey(encryptedData.sender_public_key)
      const sharedKey = await deriveSharedKey(privateKey, senderPublicKey)

      const iv = Uint8Array.from(atob(encryptedData.iv), (c) => c.charCodeAt(0))
      const ciphertext = Uint8Array.from(atob(encryptedData.ciphertext), (c) => c.charCodeAt(0))

      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        sharedKey,
        ciphertext
      )

      return new TextDecoder().decode(decrypted)
    } catch (err) {
      console.error('[Encryption] Decrypt failed:', err)
      return null
    }
  }

  // ── AI Key Grant ────────────────────────────────────────────────
  const grantAIAccess = async (conversationId, encryptedKey) => {
    try {
      await axios.post(`/api/messaging/conversations/${conversationId}/ai-access`, {
        encrypted_key: encryptedKey,
      })
      return true
    } catch (err) {
      console.error('[Encryption] Grant AI access failed:', err)
      return false
    }
  }

  const revokeAIAccess = async (conversationId) => {
    try {
      await axios.delete(`/api/messaging/conversations/${conversationId}/ai-access`)
      return true
    } catch (err) {
      console.error('[Encryption] Revoke AI access failed:', err)
      return false
    }
  }

  // ── Get Remote Key Bundle ───────────────────────────────────────
  const getKeyBundle = async (username) => {
    try {
      const { data } = await axios.get(`/api/messaging/keys/${username}`)
      return data.key_bundle
    } catch {
      return null
    }
  }

  return {
    hasKeys: readonly(hasKeys),
    isGenerating: readonly(isGenerating),
    initializeKeys,
    encrypt,
    decrypt,
    grantAIAccess,
    revokeAIAccess,
    getKeyBundle,
  }
}
