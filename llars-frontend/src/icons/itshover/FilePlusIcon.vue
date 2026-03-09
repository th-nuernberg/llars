<template>
  <svg
    class="l-its-hover__svg l-its-hover--file-plus"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Document body with LLARS asymmetric border-radius -->
    <path
      class="l-its-hover__file-plus-doc"
      d="M6.5 3H14V8H19V19.5Q19 21 17.5 21H6.5Q5 21 5 19.5V4.5Q5 3 6.5 3Z"
    />

    <!-- Fold corner -->
    <path class="l-its-hover__file-plus-fold" d="M14 3v4q0 1 1 1h4" />

    <!-- Plus sign -->
    <g class="l-its-hover__file-plus-icon">
      <path d="M12 10.5v5" stroke-width="1.8" />
      <path d="M9.5 13h5" stroke-width="1.8" />
    </g>
  </svg>
</template>

<style>
/* File Plus — LLARS document style with fold-corner animation */
.l-its-hover__file-plus-doc {
  transition: all 0.25s ease;
}

.l-its-hover__file-plus-fold {
  fill: none;
  transition: transform 0.3s ease;
  transform-origin: 14px 3px;
}

.l-its-hover__file-plus-icon {
  stroke: currentColor;
  transform-origin: 12px 13px;
  transition: all 0.25s ease;
}

/* Hover: fold peels, plus pops with accent color */
:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon, .v-list-item:hover .v-icon, .icon-wrapper:hover .v-icon)
.l-its-hover--file-plus .l-its-hover__file-plus-fold {
  transform: translate(1px, -1px) rotate(-8deg);
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon, .v-list-item:hover .v-icon, .icon-wrapper:hover .v-icon)
.l-its-hover--file-plus .l-its-hover__file-plus-icon {
  transform: scale(1.12);
  stroke: var(--llars-primary, #b0ca97);
}
</style>
