# PromptEngineering Composables

Refactored composables for the PromptEngineeringDetail component.

## Overview

This directory contains Vue 3 Composition API composables that extract and organize the business logic from the PromptEngineeringDetail component.

## Composables

### useSnackbar.js (21 lines)
**Purpose:** Notification system for user feedback

**Exports:**
- `showSnackbar` (ref) - Visibility state
- `snackbarMessage` (ref) - Current message
- `showMessage(message)` - Display notification

**Usage:**
```javascript
const { showMessage } = useSnackbar()
showMessage('Block created successfully!')
```

---

### useDialogs.js (90 lines)
**Purpose:** Centralized dialog state management

**Exports:**
- Add Block Dialog: `showAddBlockDialog`, `newBlockName`, `closeAddBlockDialog`
- Delete Block Dialog: `showDeleteBlockDialog`, `blockToDelete`, `openDeleteBlockDialog`, `closeDeleteBlockDialog`
- Upload Choice Dialog: `showUploadChoiceDialog`, `pendingJsonData`, `openUploadChoiceDialog`, `closeUploadChoiceDialog`
- Block Title Edit: `editingBlockId`, `editingBlockTitle`, `startEditBlockTitle`, `resetBlockTitleEdit`
- Test Prompt: `showTestPromptDialog`, `openTestPromptDialog`

**Usage:**
```javascript
const {
  showAddBlockDialog,
  newBlockName,
  closeAddBlockDialog
} = useDialogs()
```

---

### usePromptDetails.js (33 lines)
**Purpose:** Fetch and manage prompt metadata

**Parameters:**
- `promptId` (computed) - ID of the current prompt

**Exports:**
- `promptName` (ref) - Name of the prompt
- `promptOwner` (ref) - Username of owner
- `sharedWithUsers` (ref) - Array of shared users
- `fetchPromptDetails()` - Async fetch function

**Usage:**
```javascript
const { promptName, promptOwner, fetchPromptDetails } = usePromptDetails(promptId)
await fetchPromptDetails()
```

---

### useYjsCollaboration.js (92 lines)
**Purpose:** YJS and Socket.IO real-time collaboration

**Parameters:**
- `roomId` (computed) - Room identifier
- `username` (string) - Current user
- `onProcessYDoc` (function) - Callback when YDoc updates
- `onUpdateCursor` (function) - Callback for cursor updates

**Exports:**
- `ydoc` (ref) - YJS document instance
- `socket` (ref) - Socket.IO connection
- `users` (ref) - Connected users object
- `initialize()` - Setup connection
- `cleanup()` - Disconnect and cleanup

**Usage:**
```javascript
const collaboration = useYjsCollaboration(
  roomId,
  username,
  () => processYDoc(),
  (userId, cursor) => updateCursor(userId, cursor)
)
collaboration.initialize()
```

---

### usePromptBlocks.js (253 lines)
**Purpose:** Block CRUD operations and management

**Parameters:**
- `ydoc` (ref) - YJS document
- `roomId` (computed) - Room identifier
- `socket` (ref) - Socket.IO connection
- `showMessage` (function) - Notification callback

**Exports:**
- `blocks` (ref) - Array of blocks
- `sortedBlocks` (computed) - Sorted and settable blocks
- `processYDoc()` - Parse YDoc into blocks
- `createBlock(blockName)` - Create new block
- `deleteBlock(block)` - Delete block
- `saveBlockTitle(block, newTitle)` - Update block title
- `handleJsonUpload(jsonData, override)` - Import JSON blocks
- `assemblePrompt()` - Concatenate all blocks

**Usage:**
```javascript
const { blocks, createBlock, deleteBlock } = usePromptBlocks(
  ydoc,
  roomId,
  socket,
  showMessage
)
createBlock('New Block')
```

---

### useQuillEditor.js (278 lines)
**Purpose:** Quill editor initialization and management

**Parameters:**
- `ydoc` (ref) - YJS document
- `socket` (ref) - Socket.IO connection
- `roomId` (computed) - Room identifier

**Exports:**
- `editorsMap` (Map) - DOM element references
- `editors` (Map) - Quill editor instances
- `bindings` (Map) - YJS bindings
- `cursorsModules` (Map) - Cursor modules
- `editorCount` (ref) - Count of active editors
- `initializeEditor(block)` - Setup editor for block
- `setEditorRef(el, block)` - Register DOM ref and initialize
- `updateCursor(userId, cursor)` - Update remote cursor
- `cleanupEditor(blockId)` - Remove editor
- `cleanupAll()` - Cleanup all editors
- `applyHighlightingToAll()` - Highlight placeholders
- `removeCursorForUser(userId)` - Remove user cursor

**Usage:**
```javascript
const { setEditorRef } = useQuillEditor(
  ydoc,
  socket,
  roomId
)
setEditorRef(el, block)
```

## Architecture

```
PromptEngineeringDetail.vue
├── Template (UI)
└── Script Setup
    ├── useSnackbar() → Notifications
    ├── useDialogs() → Dialog states
    ├── usePromptDetails() → Metadata
    ├── useYjsCollaboration() → Real-time sync
    ├── usePromptBlocks() → Block management
    └── useQuillEditor() → Editor instances
```

## Benefits

1. **Separation of Concerns**: Each composable has a single responsibility
2. **Reusability**: Logic can be reused in other components
3. **Testability**: Composables can be unit tested independently
4. **Maintainability**: Smaller, focused files are easier to maintain
5. **Type Safety**: Clear interfaces for inputs/outputs

## Testing

Each composable can be tested independently:

```javascript
import { usePromptBlocks } from './usePromptBlocks'

describe('usePromptBlocks', () => {
  it('should create a new block', () => {
    const { createBlock } = usePromptBlocks(ydoc, roomId, socket, vi.fn())
    const result = createBlock('Test Block')
    expect(result).toBe(true)
  })
})
```

## Future Improvements

1. Add TypeScript type definitions
2. Add comprehensive JSDoc comments
3. Create unit tests for each composable
4. Extract utility functions (debounce, etc.)
5. Add error boundaries and handling
