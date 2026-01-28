<template>
  <svg
    class="l-its-hover__svg l-its-hover--batch-generation"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Back document - only visible corner (top and right edge) -->
    <path class="l-its-hover__batch-doc l-its-hover__batch-doc--back" d="M7.5 2h9a1.5 1.5 0 0 1 1.5 1.5v4" />

    <!-- Front document (main) -->
    <rect class="l-its-hover__batch-doc l-its-hover__batch-doc--front" x="4" y="5" width="12" height="15" rx="1.5" />

    <!-- Text lines in front document -->
    <line class="l-its-hover__batch-line" x1="6.5" y1="9" x2="11" y2="9" />
    <line class="l-its-hover__batch-line" x1="6.5" y1="12" x2="13.5" y2="12" />
    <line class="l-its-hover__batch-line" x1="6.5" y1="15" x2="10" y2="15" />

    <!-- AI Sparkles (small cross pattern) -->
    <g class="l-its-hover__batch-sparkles">
      <path class="l-its-hover__batch-sparkle l-its-hover__batch-sparkle--one" d="M20 11v2M19 12h2" />
      <path class="l-its-hover__batch-sparkle l-its-hover__batch-sparkle--two" d="M21 16v1.5M20.25 16.75h1.5" />
    </g>
  </svg>
</template>
