<template>
  <svg
    class="l-its-hover__svg l-its-hover--folder-plus"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Folder body with LLARS asymmetric corners -->
    <path
      class="l-its-hover__folder-plus-body"
      d="M4 7.5Q4 6 5.5 6H9L11 8H18.5Q20 8 20 9.5V18Q20 19.5 18.5 19.5H5.5Q4 19.5 4 18Z"
    />

    <!-- Folder tab (subtle fill) -->
    <path
      class="l-its-hover__folder-plus-tab"
      d="M4 7.5Q4 6 5.5 6H9L11 8H4Z"
      fill="currentColor"
      stroke="none"
      opacity="0.12"
    />

    <!-- Folder lid — lifts on hover -->
    <path
      class="l-its-hover__folder-plus-lid"
      d="M4 9.5H20"
      stroke-width="1.2"
      opacity="0.2"
    />

    <!-- Plus sign -->
    <g class="l-its-hover__folder-plus-icon">
      <path d="M12 11v5" stroke-width="1.8" />
      <path d="M9.5 13.5h5" stroke-width="1.8" />
    </g>
  </svg>
</template>

<style>
/* Folder Plus — LLARS style with lid-lift animation */
.l-its-hover__folder-plus-body {
  transition: all 0.25s ease;
}

.l-its-hover__folder-plus-tab {
  transition: opacity 0.25s ease;
}

.l-its-hover__folder-plus-lid {
  transition: all 0.3s ease;
  transform-origin: 4px 9.5px;
}

.l-its-hover__folder-plus-icon {
  stroke: currentColor;
  transform-origin: 12px 13.5px;
  transition: all 0.25s ease;
}

/* Hover: lid lifts, tab brightens, plus pops */
:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon, .v-list-item:hover .v-icon, .icon-wrapper:hover .v-icon)
.l-its-hover--folder-plus .l-its-hover__folder-plus-body {
  transform: translateY(-1px);
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon, .v-list-item:hover .v-icon, .icon-wrapper:hover .v-icon)
.l-its-hover--folder-plus .l-its-hover__folder-plus-tab {
  opacity: 0.22;
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon, .v-list-item:hover .v-icon, .icon-wrapper:hover .v-icon)
.l-its-hover--folder-plus .l-its-hover__folder-plus-lid {
  transform: translateY(-1.5px);
  opacity: 0.35;
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon, .v-list-item:hover .v-icon, .icon-wrapper:hover .v-icon)
.l-its-hover--folder-plus .l-its-hover__folder-plus-icon {
  transform: scale(1.12);
  stroke: var(--llars-primary, #b0ca97);
}
</style>
