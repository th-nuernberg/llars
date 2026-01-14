<template>
  <svg
    class="l-its-hover__svg l-its-hover--file-plus"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- File body -->
    <path class="l-its-hover__file-plus-outline" d="M7 3h7" />
    <path
      class="l-its-hover__file-plus-outline"
      d="M19 8v12a1 1 0 0 1 -1 1H7a1 1 0 0 1 -1 -1V4a1 1 0 0 1 1 -1"
    />
    <!-- File fold -->
    <path class="l-its-hover__file-plus-crease" d="M14 3L19 8" />
    <path class="l-its-hover__file-plus-fold" d="M14 3v5h5" />
    <!-- Plus sign -->
    <g class="l-its-hover__file-plus-icon">
      <path d="M12 11v6" />
      <path d="M9 14h6" />
    </g>
  </svg>
</template>

<style>
/* File Plus icon - hover animation */
.l-its-hover--file-plus {
  --plus-color: var(--llars-success, #98d4bb);
}

.l-its-hover__file-plus-outline,
.l-its-hover__file-plus-crease {
  transition: all 0.25s ease;
}

.l-its-hover__file-plus-fold {
  transform-origin: 14px 3px;
  transition: transform 0.3s ease;
}

.l-its-hover__file-plus-icon {
  stroke: var(--plus-color);
  stroke-width: 2;
  transform-origin: 12px 14px;
  transition: all 0.25s ease;
}

/* Hover effects */
:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--file-plus .l-its-hover__file-plus-fold {
  transform: rotate(-15deg);
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--file-plus .l-its-hover__file-plus-icon {
  transform: scale(1.15);
  stroke: var(--llars-primary, #b0ca97);
}
</style>
