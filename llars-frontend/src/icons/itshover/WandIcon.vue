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
    <!-- Wand stick - thicker diagonal, aligned to star -->
    <g class="l-its-hover__wand-stick">
      <path d="M4 20L13 11" stroke-width="2.5" />
      <!-- Handle/grip at bottom -->
      <circle cx="3" cy="21" r="1.5" fill="currentColor" stroke="none" />
    </g>

    <!-- Star tip - 4-point star centered on wand extension at (16, 8) -->
    <g class="l-its-hover__wand-tip">
      <path d="M16 4L17 6.5L19.5 7.5L17 8.5L16 11L15 8.5L12.5 7.5L15 6.5Z" fill="currentColor" stroke="none" />
    </g>

    <!-- Magic sparkles - distributed around the star -->
    <g class="l-its-hover__wand-sparkles">
      <path class="l-its-hover__wand-sparkle l-its-hover__wand-sparkle--one" d="M11 3v1.5M10.25 3.75h1.5" />
      <path class="l-its-hover__wand-sparkle l-its-hover__wand-sparkle--two" d="M21 4v1.5M20.25 4.75h1.5" />
      <path class="l-its-hover__wand-sparkle l-its-hover__wand-sparkle--three" d="M20 12v1.5M19.25 12.75h1.5" />
    </g>
  </svg>
</template>
