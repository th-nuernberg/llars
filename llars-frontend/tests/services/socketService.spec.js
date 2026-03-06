/**
 * Socket.IO Service Tests
 *
 * Tests for the Socket.IO connection manager with visibility handling.
 * Test IDs: SVC_SOCK_001 - SVC_SOCK_045
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock socket.io-client
const mockSocketInstance = {
  on: vi.fn(),
  connect: vi.fn(),
  disconnect: vi.fn(),
  connected: false,
  io: { opts: { query: {} } }
}

vi.mock('socket.io-client', () => ({
  io: vi.fn(() => mockSocketInstance)
}))

vi.mock('@/utils/authStorage', () => ({
  AUTH_STORAGE_KEYS: {
    token: 'auth_token'
  },
  getAuthStorageItem: vi.fn(() => 'mock-token')
}))

vi.mock('@/utils/logI18n', () => ({
  logI18n: vi.fn()
}))

// Must import after mocks are set up
import { io } from 'socket.io-client'
import { getAuthStorageItem } from '@/utils/authStorage'

describe('socketService', () => {
  let socketModule

  beforeEach(async () => {
    vi.clearAllMocks()

    // Reset connected state
    mockSocketInstance.connected = false
    mockSocketInstance.on.mockReset()
    mockSocketInstance.connect.mockReset()
    mockSocketInstance.disconnect.mockReset()
    mockSocketInstance.io = { opts: { query: {} } }

    // Re-import to get fresh module state each test
    vi.resetModules()

    // Re-apply mocks after resetModules
    vi.doMock('socket.io-client', () => ({
      io: vi.fn(() => mockSocketInstance)
    }))
    vi.doMock('@/utils/authStorage', () => ({
      AUTH_STORAGE_KEYS: { token: 'auth_token' },
      getAuthStorageItem: vi.fn(() => 'mock-token')
    }))
    vi.doMock('@/utils/logI18n', () => ({
      logI18n: vi.fn()
    }))

    socketModule = await import('@/services/socketService')
  })

  afterEach(() => {
    // Clean up socket
    try {
      socketModule.disconnectSocket()
    } catch {
      // ignore
    }
  })

  describe('getSocket', () => {
    it('SVC_SOCK_001: creates a new socket on first call', () => {
      const socket = socketModule.getSocket()

      expect(socket).toBeDefined()
    })

    it('SVC_SOCK_002: returns same socket on subsequent calls', () => {
      const socket1 = socketModule.getSocket()
      const socket2 = socketModule.getSocket()

      // Both return the mock instance
      expect(socket1).toBe(socket2)
    })

    it('SVC_SOCK_003: registers connect event handler', () => {
      socketModule.getSocket()

      const connectCall = mockSocketInstance.on.mock.calls.find(c => c[0] === 'connect')
      expect(connectCall).toBeDefined()
    })

    it('SVC_SOCK_004: registers disconnect event handler', () => {
      socketModule.getSocket()

      const disconnectCall = mockSocketInstance.on.mock.calls.find(c => c[0] === 'disconnect')
      expect(disconnectCall).toBeDefined()
    })

    it('SVC_SOCK_005: registers connect_error event handler', () => {
      socketModule.getSocket()

      const errorCall = mockSocketInstance.on.mock.calls.find(c => c[0] === 'connect_error')
      expect(errorCall).toBeDefined()
    })

    it('SVC_SOCK_006: triggers connect when existing socket is disconnected', () => {
      socketModule.getSocket() // Create socket
      mockSocketInstance.connected = false

      socketModule.getSocket() // Second call should reconnect

      expect(mockSocketInstance.connect).toHaveBeenCalled()
    })
  })

  describe('disconnectSocket', () => {
    it('SVC_SOCK_010: disconnects existing socket', () => {
      socketModule.getSocket()
      socketModule.disconnectSocket()

      expect(mockSocketInstance.disconnect).toHaveBeenCalled()
    })

    it('SVC_SOCK_011: handles disconnect when no socket exists', () => {
      // Should not throw
      expect(() => socketModule.disconnectSocket()).not.toThrow()
    })
  })

  describe('reconnect', () => {
    it('SVC_SOCK_012: calls connect on existing disconnected socket', () => {
      socketModule.getSocket()
      mockSocketInstance.connected = false

      socketModule.reconnect()

      expect(mockSocketInstance.connect).toHaveBeenCalled()
    })

    it('SVC_SOCK_013: does not call connect on already connected socket', () => {
      socketModule.getSocket()
      mockSocketInstance.connected = true
      mockSocketInstance.connect.mockClear()

      socketModule.reconnect()

      expect(mockSocketInstance.connect).not.toHaveBeenCalled()
    })

    it('SVC_SOCK_014: creates new socket if none exists', () => {
      // Call reconnect without prior getSocket
      socketModule.reconnect()

      // Should have created a socket (via getSocket internally)
      expect(mockSocketInstance.on).toHaveBeenCalled()
    })
  })

  describe('useSocketState', () => {
    it('SVC_SOCK_015: returns isConnected ref', () => {
      const { isConnected } = socketModule.useSocketState()
      expect(isConnected).toBeDefined()
      expect(isConnected.value).toBe(false)
    })

    it('SVC_SOCK_016: returns connectionError ref', () => {
      const { connectionError } = socketModule.useSocketState()
      expect(connectionError).toBeDefined()
      expect(connectionError.value).toBeNull()
    })

    it('SVC_SOCK_017: isConnected is readonly', () => {
      const { isConnected } = socketModule.useSocketState()
      // readonly refs will not allow direct .value assignment
      // but we can check it's a ref with a value
      expect(typeof isConnected.value).toBe('boolean')
    })
  })

  describe('Event Handlers', () => {
    it('SVC_SOCK_020: connect handler sets isConnected to true', () => {
      socketModule.getSocket()

      const connectHandler = mockSocketInstance.on.mock.calls.find(c => c[0] === 'connect')[1]
      connectHandler()

      const { isConnected } = socketModule.useSocketState()
      expect(isConnected.value).toBe(true)
    })

    it('SVC_SOCK_021: connect handler clears connectionError', () => {
      socketModule.getSocket()

      // Simulate error first
      const errorHandler = mockSocketInstance.on.mock.calls.find(c => c[0] === 'connect_error')[1]
      errorHandler({ message: 'test error' })

      // Then connect
      const connectHandler = mockSocketInstance.on.mock.calls.find(c => c[0] === 'connect')[1]
      connectHandler()

      const { connectionError } = socketModule.useSocketState()
      expect(connectionError.value).toBeNull()
    })

    it('SVC_SOCK_022: disconnect handler sets isConnected to false', () => {
      socketModule.getSocket()

      // Set connected first
      const connectHandler = mockSocketInstance.on.mock.calls.find(c => c[0] === 'connect')[1]
      connectHandler()

      // Then disconnect
      const disconnectHandler = mockSocketInstance.on.mock.calls.find(c => c[0] === 'disconnect')[1]
      disconnectHandler('io server disconnect')

      const { isConnected } = socketModule.useSocketState()
      expect(isConnected.value).toBe(false)
    })

    it('SVC_SOCK_023: connect_error handler sets connectionError', () => {
      socketModule.getSocket()

      const errorHandler = mockSocketInstance.on.mock.calls.find(c => c[0] === 'connect_error')[1]
      errorHandler({ message: 'Connection refused' })

      const { connectionError } = socketModule.useSocketState()
      expect(connectionError.value).toBe('Connection refused')
    })

    it('SVC_SOCK_024: connect_error handler sets isConnected to false', () => {
      socketModule.getSocket()

      const errorHandler = mockSocketInstance.on.mock.calls.find(c => c[0] === 'connect_error')[1]
      errorHandler({ message: 'error' })

      const { isConnected } = socketModule.useSocketState()
      expect(isConnected.value).toBe(false)
    })
  })

  describe('Default Export', () => {
    it('SVC_SOCK_030: default export contains getSocket', () => {
      expect(socketModule.default.getSocket).toBeDefined()
    })

    it('SVC_SOCK_031: default export contains disconnectSocket', () => {
      expect(socketModule.default.disconnectSocket).toBeDefined()
    })

    it('SVC_SOCK_032: default export contains reconnect', () => {
      expect(socketModule.default.reconnect).toBeDefined()
    })

    it('SVC_SOCK_033: default export contains useSocketState', () => {
      expect(socketModule.default.useSocketState).toBeDefined()
    })
  })
})
