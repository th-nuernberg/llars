/**
 * Home Tiles Contract Tests
 *
 * Validates the structure and content of home_tiles.contract.json.
 * This is the source-of-truth for Home page tiles, routes, and role visibility.
 * Test IDs: TILES_001 - TILES_030
 */

import { describe, it, expect } from 'vitest'
import tilesContract from '@/config/home_tiles.contract.json'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const VALID_ROLES = ['evaluator', 'researcher', 'chatbot_manager', 'admin']
const VALID_CATEGORIES = ['research', 'rating', 'ai', 'admin', 'all']

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('home_tiles.contract.json', () => {

  // =========================================================================
  // Top-level structure
  // =========================================================================

  describe('top-level structure', () => {
    it('TILES_001: has a version string', () => {
      expect(typeof tilesContract.version).toBe('string')
      expect(tilesContract.version.length).toBeGreaterThan(0)
    })

    it('TILES_002: has a description string', () => {
      expect(typeof tilesContract.description).toBe('string')
      expect(tilesContract.description.length).toBeGreaterThan(0)
    })

    it('TILES_003: has roles_order array', () => {
      expect(Array.isArray(tilesContract.roles_order)).toBe(true)
      expect(tilesContract.roles_order).toEqual(VALID_ROLES)
    })

    it('TILES_004: has tiles array', () => {
      expect(Array.isArray(tilesContract.tiles)).toBe(true)
      expect(tilesContract.tiles.length).toBeGreaterThan(0)
    })
  })

  // =========================================================================
  // Tile structure validation
  // =========================================================================

  describe('tile structure', () => {
    it('TILES_005: every tile has a name string', () => {
      for (const tile of tilesContract.tiles) {
        expect(typeof tile.name, `tile missing name`).toBe('string')
        expect(tile.name.length, `tile name should not be empty`).toBeGreaterThan(0)
      }
    })

    it('TILES_006: every tile has a route string', () => {
      for (const tile of tilesContract.tiles) {
        expect(typeof tile.route, `${tile.name}: route should be string`).toBe('string')
        expect(tile.route.length, `${tile.name}: route should not be empty`).toBeGreaterThan(0)
      }
    })

    it('TILES_007: every tile route starts with /', () => {
      for (const tile of tilesContract.tiles) {
        expect(tile.route[0], `${tile.name}: route should start with /`).toBe('/')
      }
    })

    it('TILES_008: every tile has allowed_roles array', () => {
      for (const tile of tilesContract.tiles) {
        expect(Array.isArray(tile.allowed_roles), `${tile.name}: allowed_roles should be array`).toBe(true)
        expect(tile.allowed_roles.length, `${tile.name}: allowed_roles should not be empty`).toBeGreaterThan(0)
      }
    })

    it('TILES_009: all allowed_roles contain only valid roles', () => {
      for (const tile of tilesContract.tiles) {
        for (const role of tile.allowed_roles) {
          expect(VALID_ROLES, `${tile.name}: invalid role '${role}'`).toContain(role)
        }
      }
    })

    it('TILES_010: every tile has a category string', () => {
      for (const tile of tilesContract.tiles) {
        expect(typeof tile.category, `${tile.name}: category should be string`).toBe('string')
      }
    })

    it('TILES_011: all categories are valid', () => {
      for (const tile of tilesContract.tiles) {
        expect(VALID_CATEGORIES, `${tile.name}: invalid category '${tile.category}'`).toContain(tile.category)
      }
    })

    it('TILES_012: tile names are unique', () => {
      const names = tilesContract.tiles.map(t => t.name)
      const uniqueNames = new Set(names)
      expect(uniqueNames.size, 'Duplicate tile names found').toBe(names.length)
    })

    it('TILES_013: tile routes are unique', () => {
      const routes = tilesContract.tiles.map(t => t.route)
      const uniqueRoutes = new Set(routes)
      expect(uniqueRoutes.size, 'Duplicate tile routes found').toBe(routes.length)
    })

    it('TILES_014: no tile has duplicate roles in allowed_roles', () => {
      for (const tile of tilesContract.tiles) {
        const unique = new Set(tile.allowed_roles)
        expect(unique.size, `${tile.name}: duplicate roles`).toBe(tile.allowed_roles.length)
      }
    })
  })

  // =========================================================================
  // Specific tiles existence
  // =========================================================================

  describe('required tiles', () => {
    const requiredTiles = [
      'Prompt Engineering',
      'Batch Generation',
      'Evaluation',
      'Scenario Manager',
      'Chatbot',
      'Admin Dashboard',
      'User Settings'
    ]

    it('TILES_015: contains all required tiles', () => {
      const tileNames = tilesContract.tiles.map(t => t.name)
      for (const required of requiredTiles) {
        expect(tileNames, `Missing required tile: ${required}`).toContain(required)
      }
    })
  })

  // =========================================================================
  // Role-specific visibility
  // =========================================================================

  describe('role visibility', () => {
    function getTilesForRole(role) {
      return tilesContract.tiles.filter(t => t.allowed_roles.includes(role))
    }

    it('TILES_016: admin can access all tiles', () => {
      const adminTiles = getTilesForRole('admin')
      expect(adminTiles.length).toBe(tilesContract.tiles.length)
    })

    it('TILES_017: Admin Dashboard is admin-only', () => {
      const dashboard = tilesContract.tiles.find(t => t.name === 'Admin Dashboard')
      expect(dashboard.allowed_roles).toEqual(['admin'])
    })

    it('TILES_018: User Settings is accessible to all roles', () => {
      const settings = tilesContract.tiles.find(t => t.name === 'User Settings')
      expect(settings.allowed_roles).toEqual(VALID_ROLES)
    })

    it('TILES_019: evaluator can access Evaluation', () => {
      const evaluation = tilesContract.tiles.find(t => t.name === 'Evaluation')
      expect(evaluation.allowed_roles).toContain('evaluator')
    })

    it('TILES_020: chatbot_manager can access Chatbot Admin', () => {
      const chatbotAdmin = tilesContract.tiles.find(t => t.name === 'Chatbot Admin')
      expect(chatbotAdmin.allowed_roles).toContain('chatbot_manager')
    })

    it('TILES_021: chatbot_manager can access RAG Admin', () => {
      const ragAdmin = tilesContract.tiles.find(t => t.name === 'RAG Admin')
      expect(ragAdmin.allowed_roles).toContain('chatbot_manager')
    })

    it('TILES_022: evaluator cannot access Admin Dashboard', () => {
      const dashboard = tilesContract.tiles.find(t => t.name === 'Admin Dashboard')
      expect(dashboard.allowed_roles).not.toContain('evaluator')
    })

    it('TILES_023: Chatbot Arena is admin-only', () => {
      const arena = tilesContract.tiles.find(t => t.name === 'Chatbot Arena')
      expect(arena.allowed_roles).toEqual(['admin'])
    })
  })

  // =========================================================================
  // Route patterns
  // =========================================================================

  describe('route patterns', () => {
    it('TILES_024: Evaluation routes to /evaluation', () => {
      const tile = tilesContract.tiles.find(t => t.name === 'Evaluation')
      expect(tile.route).toBe('/evaluation')
    })

    it('TILES_025: Scenario Manager routes to /scenarios', () => {
      const tile = tilesContract.tiles.find(t => t.name === 'Scenario Manager')
      expect(tile.route).toBe('/scenarios')
    })

    it('TILES_026: Chatbot routes to /chat', () => {
      const tile = tilesContract.tiles.find(t => t.name === 'Chatbot')
      expect(tile.route).toBe('/chat')
    })

    it('TILES_027: Admin Dashboard routes to /admin with tab param', () => {
      const tile = tilesContract.tiles.find(t => t.name === 'Admin Dashboard')
      expect(tile.route).toBe('/admin?tab=overview')
    })

    it('TILES_028: Pipeline routes to /pipeline', () => {
      const pipeline = tilesContract.tiles.find(t => t.name === 'Pipeline')
      expect(pipeline).toBeDefined()
      expect(pipeline.route).toBe('/pipeline')
    })
  })

  // =========================================================================
  // Category distribution
  // =========================================================================

  describe('category distribution', () => {
    it('TILES_029: has tiles in multiple categories', () => {
      const categories = new Set(tilesContract.tiles.map(t => t.category))
      expect(categories.size).toBeGreaterThanOrEqual(3)
    })

    it('TILES_030: has at least one tile in research category', () => {
      const research = tilesContract.tiles.filter(t => t.category === 'research')
      expect(research.length).toBeGreaterThan(0)
    })
  })
})
