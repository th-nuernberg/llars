# Frontend-Komponenten

Diese Dokumentation beschreibt die wiederverwendbaren Vue-Komponenten des LLARS Design Systems.

## Übersicht

Das LLARS Design System bietet eine Sammlung von global verfügbaren Komponenten mit einheitlichem Design:

| Komponente | Beschreibung |
|------------|--------------|
| `LBtn` | Standard-Button mit Varianten |
| `LIconBtn` | Icon-Button mit Tooltip |
| `LIcon` | Icon-Wrapper für MDI Icons |
| `LTag` | Status-Tags und Labels |
| `LCheckbox` | Checkbox mit Label |
| `LFloatingWindow` | Draggable Floating Window |
| `LCard` | Card-Container |
| `LLoading` | Loading-Spinner |
| ... | weitere Komponenten |

## Design-Grundlagen

### LLARS Signature: Asymmetrischer Border-Radius

```css
/* Standard für Buttons und Windows */
border-radius: 16px 4px 16px 4px;

/* Klein für Tags */
border-radius: 6px 2px 6px 2px;

/* Mini für Icons */
border-radius: 8px 2px 8px 2px;
```

### Farbpalette

| Farbe | Hex | CSS Variable | Verwendung |
|-------|-----|--------------|------------|
| Primary | `#b0ca97` | `--llars-primary` | Hauptaktionen, Standard |
| Secondary | `#D1BC8A` | `--llars-secondary` | Sekundäre Aktionen |
| Accent | `#88c4c8` | `--llars-accent` | Hervorhebungen |
| Success | `#98d4bb` | `--llars-success` | Erfolg |
| Warning | `#f0c674` | `--llars-warning` | Warnungen |
| Danger | `#e8a087` | `--llars-danger` | Destruktive Aktionen |
| AI | `#9B59B6` | - | KI-Features |

---

## LFloatingWindow

Ein draggable, resizable Floating Window für Tool-Panels, Dialoge und Assistenten.

### Features

- **Draggable Header:** Fenster per Drag & Drop verschieben
- **Resizable:** Resize-Handle rechts unten
- **Position Persistenz:** Speichert Position/Größe in localStorage
- **LLARS Design:** Asymmetrischer Border-Radius, Farbthemen
- **Flexible Slots:** Tags, Header-Actions, Content, Footer
- **Built-in Buttons:** Close, Minimize, Maximize, Refresh

### Props

| Prop | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `modelValue` | `Boolean` | `false` | v-model für Sichtbarkeit |
| `title` | `String` | *required* | Fenstertitel |
| `icon` | `String` | `null` | Header-Icon (mdi-*) |
| `iconSize` | `Number/String` | `18` | Icon-Größe |
| `color` | `String` | `'primary'` | Farbthema (siehe unten) |
| `width` | `Number/String` | `400` | Initiale Breite |
| `height` | `Number/String` | `300` | Initiale Höhe |
| `minWidth` | `Number` | `300` | Minimale Breite |
| `minHeight` | `Number` | `200` | Minimale Höhe |
| `maxWidth` | `Number` | `null` | Max Breite (null = viewport - 40px) |
| `maxHeight` | `Number` | `null` | Max Höhe (null = viewport - 60px) |
| `resizable` | `Boolean` | `true` | Größenänderung erlauben |
| `storageKey` | `String` | `null` | localStorage Key für Persistenz |
| `initialX` | `Number` | `null` | Start-X (null = zentriert) |
| `initialY` | `Number` | `null` | Start-Y (null = zentriert) |
| `showClose` | `Boolean` | `true` | Close-Button anzeigen |
| `showMinimize` | `Boolean` | `false` | Minimize-Button anzeigen |
| `showMaximize` | `Boolean` | `false` | Maximize-Button anzeigen |
| `showRefresh` | `Boolean` | `false` | Refresh-Button anzeigen |
| `refreshLoading` | `Boolean` | `false` | Refresh-Loading-State |
| `refreshTooltip` | `String` | `null` | Refresh-Button Tooltip |
| `zIndex` | `Number` | `9999` | Z-Index |

### Farbthemen

```vue
<!-- Verfügbare Werte für color prop -->
color="primary"    <!-- Grün - Standard -->
color="secondary"  <!-- Gold -->
color="accent"     <!-- Türkis -->
color="success"    <!-- Erfolg-Grün -->
color="warning"    <!-- Gelb -->
color="danger"     <!-- Rot -->
color="ai"         <!-- Lila - für KI-Features -->
```

### Slots

| Slot | Beschreibung |
|------|--------------|
| `default` | Hauptinhalt des Fensters |
| `tags` | Status-Tags im Header (zwischen Titel und Actions) |
| `header-actions` | Zusätzliche Buttons vor den Built-in Buttons |
| `footer` | Optionaler Footer (z.B. für Input + Submit) |

### Events

| Event | Payload | Beschreibung |
|-------|---------|--------------|
| `update:modelValue` | `Boolean` | Sichtbarkeit geändert |
| `refresh` | - | Refresh-Button geklickt |
| `minimize` | - | Minimize-Button geklickt |
| `maximize` | - | Fenster maximiert |
| `restore` | - | Aus Maximierung wiederhergestellt |
| `close` | - | Fenster geschlossen |
| `drag-start` | - | Drag gestartet |
| `drag-end` | - | Drag beendet |
| `resize-start` | - | Resize gestartet |
| `resize-end` | - | Resize beendet |

### Beispiel: Einfaches Fenster

```vue
<template>
  <LBtn @click="showWindow = true">Öffnen</LBtn>

  <LFloatingWindow
    v-model="showWindow"
    title="Einstellungen"
    icon="mdi-cog"
    color="accent"
  >
    <div class="pa-4">
      <p>Fensterinhalt hier</p>
    </div>
  </LFloatingWindow>
</template>

<script setup>
import { ref } from 'vue'
const showWindow = ref(false)
</script>
```

### Beispiel: Git Panel mit Tags und Footer

```vue
<template>
  <LFloatingWindow
    :model-value="showGitPanel"
    title="Git-Panel"
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
    <!-- Status Tags -->
    <template #tags>
      <LTag v-if="changedCount > 0" variant="warning" size="small">
        {{ changedCount }} geändert
      </LTag>
      <LTag v-else variant="success" size="small">
        Synchron
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
        placeholder="Commit-Nachricht..."
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

### Beispiel: KI-Assistent

```vue
<template>
  <LFloatingWindow
    v-model="showAssistant"
    title="KI-Assistent"
    icon="mdi-robot-happy"
    color="ai"
    :width="380"
    :height="500"
    storage-key="llars-ai-assistant"
  >
    <template #tags>
      <LTag v-if="hasSelection" variant="accent" size="small">
        <LIcon size="12">mdi-selection</LIcon>
        Auswahl
      </LTag>
    </template>

    <ChatMessages :messages="messages" />
    <ChatInput v-model="input" @send="sendMessage" />
  </LFloatingWindow>
</template>
```

### Position Persistenz

Wenn `storageKey` gesetzt ist, werden Position und Größe automatisch in localStorage gespeichert:

```javascript
// Gespeichertes Format
{
  "x": 100,      // X-Position
  "y": 50,       // Y-Position
  "width": 800,  // Breite
  "height": 500  // Höhe
}
```

Das Fenster öffnet sich beim nächsten Mal an der gleichen Position.

### Exposed Methods

```vue
<template>
  <LFloatingWindow ref="windowRef" ... />
</template>

<script setup>
const windowRef = ref(null)

// Verfügbare Methoden:
windowRef.value.close()           // Fenster schließen
windowRef.value.toggleMaximize()  // Maximieren/Wiederherstellen

// Verfügbare Refs:
windowRef.value.position     // { x, y }
windowRef.value.size         // { width, height }
windowRef.value.isMaximized  // Boolean
</script>
```

---

## Best Practices

### Wann LFloatingWindow verwenden?

✅ **Verwenden für:**
- Tool-Panels (Git, Debug, etc.)
- KI-Assistenten
- Detailansichten die nicht den Hauptinhalt blockieren
- Fenster die der User frei positionieren soll

❌ **Nicht verwenden für:**
- Bestätigungs-Dialoge → `v-dialog`
- Modale Aktionen → `v-dialog`
- Vollbild-Editoren → eigene View
- Permanente Sidebars → normale Sidebar-Komponente

### Storage Keys

Verwende eindeutige, beschreibende Storage Keys:

```vue
<!-- Gut -->
storage-key="llars-git-panel"
storage-key="llars-ai-assistant-latex"
storage-key="llars-prompt-git-panel"

<!-- Schlecht -->
storage-key="window1"
storage-key="panel"
```

### Responsive Größen

Setze sinnvolle Min/Max-Werte:

```vue
<LFloatingWindow
  :width="800"
  :height="500"
  :min-width="400"
  :min-height="300"
  :max-width="1200"
/>
```
