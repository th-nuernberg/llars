<template>
  <svg
    class="l-its-hover__svg l-its-hover--folder-plus"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Folder back -->
    <path
      class="l-its-hover__folder-plus-back"
      d="M3 7a2 2 0 0 1 2 -2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2H5a2 2 0 0 1 -2 -2z"
    />
    <!-- Folder tab highlight -->
    <path
      class="l-its-hover__folder-plus-tab"
      d="M3 7h6l2 -2h-4a2 2 0 0 0 -2 2z"
      fill="currentColor"
      stroke="none"
      opacity="0.15"
    />
    <!-- Plus sign -->
    <g class="l-its-hover__folder-plus-icon">
      <path d="M12 10v6" />
      <path d="M9 13h6" />
    </g>
  </svg>
</template>

<style>
/* Folder Plus icon - hover animation */
.l-its-hover--folder-plus {
  --plus-color: var(--llars-success, #98d4bb);
}

.l-its-hover__folder-plus-back {
  transition: all 0.25s ease;
}

.l-its-hover__folder-plus-tab {
  transition: opacity 0.25s ease;
}

.l-its-hover__folder-plus-icon {
  stroke: var(--plus-color);
  stroke-width: 2;
  transform-origin: 12px 13px;
  transition: all 0.25s ease;
}

/* Hover effects - folder opens slightly, plus pops */
:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--folder-plus .l-its-hover__folder-plus-back {
  transform: translateY(-1px);
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--folder-plus .l-its-hover__folder-plus-tab {
  opacity: 0.25;
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--folder-plus .l-its-hover__folder-plus-icon {
  transform: scale(1.15);
  stroke: var(--llars-primary, #b0ca97);
}
</style>
