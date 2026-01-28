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
    <!-- Wand stick - thicker diagonal -->
    <g class="l-its-hover__wand-stick">
      <path d="M5 19L15 9" stroke-width="2.5" />
      <!-- Handle/grip at bottom -->
      <circle cx="4" cy="20" r="1.5" fill="currentColor" stroke="none" />
    </g>

    <!-- Star tip - clean 4-point star -->
    <g class="l-its-hover__wand-tip">
      <path d="M18 4l1 3l3 1l-3 1l-1 3l-1-3l-3-1l3-1z" fill="currentColor" stroke="none" />
    </g>

    <!-- Magic sparkles - concentrated near tip -->
    <g class="l-its-hover__wand-sparkles">
      <path class="l-its-hover__wand-sparkle l-its-hover__wand-sparkle--one" d="M13 3v1.5M12.25 3.75h1.5" />
      <path class="l-its-hover__wand-sparkle l-its-hover__wand-sparkle--two" d="M21 10v1.5M20.25 10.75h1.5" />
    </g>
  </svg>
</template>
