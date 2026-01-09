<template>
  <svg
    class="l-its-hover__svg l-its-hover--wand"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Wand stick - diagonal line -->
    <path class="l-its-hover__wand-stick" d="M4 20L17 7" />
    <!-- Wand tip - small star -->
    <g class="l-its-hover__wand-tip">
      <path d="M19 5l0.6-1.8l0.6 1.8l1.8 0.6l-1.8 0.6l-0.6 1.8l-0.6-1.8l-1.8-0.6z" fill="currentColor" stroke="none" />
    </g>
    <!-- Magic sparkles -->
    <g class="l-its-hover__wand-sparkles">
      <path class="l-its-hover__wand-sparkle l-its-hover__wand-sparkle--one" d="M9 6v1.2M8.4 6.6h1.2" />
      <path class="l-its-hover__wand-sparkle l-its-hover__wand-sparkle--two" d="M14 11v1M13.5 11.5h1" />
      <path class="l-its-hover__wand-sparkle l-its-hover__wand-sparkle--three" d="M6 12v1M5.5 12.5h1" />
    </g>
  </svg>
</template>
