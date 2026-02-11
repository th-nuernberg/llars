# Frontend Components

This documentation describes the reusable Vue components of the LLARS design system.

## Overview

The LLARS design system provides a collection of globally available components with a consistent style:

| Component | Description |
|----------|-------------|
| `LBtn` | Standard button with variants |
| `LIconBtn` | Icon button with tooltip |
| `LIcon` | Icon wrapper for MDI icons |
| `LTag` | Status tags and labels |
| `LCheckbox` | Checkbox with label |
| `LFloatingWindow` | Draggable floating window |
| `LCard` | Card container |
| `LLoading` | Loading spinner |
| ... | more components |

## Design basics

### LLARS signature: asymmetric border radius

```css
/* Default for buttons and windows */
border-radius: 16px 4px 16px 4px;

/* Small for tags */
border-radius: 6px 2px 6px 2px;

/* Mini for icons */
border-radius: 8px 2px 8px 2px;
```

### Color palette

| Color | Hex | CSS variable | Usage |
|-------|-----|--------------|-------|
| Primary | `#b0ca97` | `--llars-primary` | Primary actions, default |
| Secondary | `#D1BC8A` | `--llars-secondary` | Secondary actions |
| Accent | `#88c4c8` | `--llars-accent` | Highlights |
| Success | `#98d4bb` | `--llars-success` | Success |
| Warning | `#f0c674` | `--llars-warning` | Warnings |
| Danger | `#e8a087` | `--llars-danger` | Destructive actions |
| AI | `#9B59B6` | - | AI features |

---

## LFloatingWindow

A draggable, resizable floating window for tool panels, dialogs, and assistants.

### Features

- **Draggable header:** move the window via drag & drop
- **Resizable:** resize handle bottom-right
- **Position persistence:** stores position/size in localStorage
- **LLARS design:** asymmetric border radius, theme colors
- **Flexible slots:** tags, header actions, content, footer
- **Built-in buttons:** close, minimize, maximize, refresh

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `modelValue` | `Boolean` | `false` | v-model for visibility |
| `title` | `String` | *required* | Window title |
| `icon` | `String` | `null` | Header icon (mdi-*) |
| `iconSize` | `Number/String` | `18` | Icon size |
| `color` | `String` | `'primary'` | Theme color (see below) |
| `width` | `Number/String` | `400` | Initial width |
| `height` | `Number/String` | `300` | Initial height |
| `minWidth` | `Number` | `300` | Minimum width |
| `minHeight` | `Number` | `200` | Minimum height |
| `maxWidth` | `Number` | `null` | Max width (null = viewport - 40px) |
| `maxHeight` | `Number` | `null` | Max height (null = viewport - 60px) |
| `resizable` | `Boolean` | `true` | Allow resize |
| `storageKey` | `String` | `null` | localStorage key for persistence |
| `initialX` | `Number` | `null` | Start X (null = centered) |
| `initialY` | `Number` | `null` | Start Y (null = centered) |
| `showClose` | `Boolean` | `true` | Show close button |
| `showMinimize` | `Boolean` | `false` | Show minimize button |
| `showMaximize` | `Boolean` | `false` | Show maximize button |
| `showRefresh` | `Boolean` | `false` | Show refresh button |
| `refreshLoading` | `Boolean` | `false` | Refresh loading state |
| `refreshTooltip` | `String` | `null` | Refresh tooltip |
| `zIndex` | `Number` | `9999` | Z-index |

### Color themes

```vue
<!-- Available values for the color prop -->
color="primary"    <!-- Green - default -->
color="secondary"  <!-- Gold -->
color="accent"     <!-- Turquoise -->
color="success"    <!-- Success green -->
color="warning"    <!-- Yellow -->
color="danger"     <!-- Red -->
color="ai"         <!-- Purple - for AI features -->
```

### Slots

| Slot | Description |
|------|-------------|
| `default` | Main window content |
| `tags` | Status tags in header (between title and actions) |
| `header-actions` | Additional buttons before built-in buttons |
| `footer` | Optional footer (e.g. input + submit) |

### Events

| Event | Payload | Description |
|-------|---------|-------------|
| `update:modelValue` | `Boolean` | Visibility changed |
| `refresh` | - | Refresh clicked |
| `minimize` | - | Minimize clicked |
| `maximize` | - | Window maximized |
| `restore` | - | Restored from maximize |
| `close` | - | Window closed |
| `drag-start` | - | Drag started |
| `drag-end` | - | Drag ended |
| `resize-start` | - | Resize started |
| `resize-end` | - | Resize ended |

### Example: simple window

```vue
<template>
  <LBtn @click="showWindow = true">Open</LBtn>

  <LFloatingWindow
    v-model="showWindow"
    title="Settings"
    icon="mdi-cog"
    color="accent"
  >
    <div class="pa-4">
      <p>Window content here</p>
    </div>
  </LFloatingWindow>
</template>

<script setup>
import { ref } from 'vue'
const showWindow = ref(false)
</script>
```

### Example: Git panel with tags and footer

```vue
<template>
  <LFloatingWindow
    :model-value="showGitPanel"
    title="Git Panel"
    icon="mdi-source-branch"
    color="primary"
    :width="800"
    :height="500"
    storage-key="llars-git-panel"
    :show-refresh="true"
    :refresh-loading="isLoading"
    @update:model-value="showGitPanel = $event"
    @refresh="refreshChanges"
  >
    <!-- Status tags -->
    <template #tags>
      <LTag v-if="changedCount > 0" variant="warning" size="small">
        {{ changedCount }} changed
      </LTag>
      <LTag v-else variant="success" size="small">
        In sync
      </LTag>
    </template>

    <!-- Content -->
    <div class="git-content">
      <FileList :files="changedFiles" />
      <DiffViewer :file="selectedFile" />
    </div>

    <!-- Footer -->
    <template #footer>
      <v-text-field
        v-model="commitMessage"
        placeholder="Commit message..."
        density="compact"
        hide-details
      />
      <LBtn variant="primary" @click="commit">
        Commit
      </LBtn>
    </template>
  </LFloatingWindow>
</template>
```

### Example: AI assistant

```vue
<template>
  <LFloatingWindow
    v-model="showAssistant"
    title="AI Assistant"
    icon="mdi-robot-happy"
    color="ai"
    :width="380"
    :height="500"
    storage-key="llars-ai-assistant"
  >
    <template #tags>
      <LTag v-if="hasSelection" variant="accent" size="small">
        <LIcon size="12">mdi-selection</LIcon>
        Selection
      </LTag>
    </template>

    <ChatMessages :messages="messages" />
    <ChatInput v-model="input" @send="sendMessage" />
  </LFloatingWindow>
</template>
```

### Position persistence

If `storageKey` is set, position and size are stored in localStorage:

```javascript
// Saved format
{
  "x": 100,      // X position
  "y": 50,       // Y position
  "width": 800,  // Width
  "height": 500  // Height
}
```

The window will open at the same position next time.
