<template>
  <svg
    class="l-its-hover__svg l-its-hover--gemini"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Gemini-inspired dual star/sparkle pattern -->
    <g class="l-its-hover__gemini-stars">
      <!-- Top star -->
      <path class="l-its-hover__gemini-star-top" d="M12 2v4M12 6l2-2M12 6l-2-2" />
      <!-- Left sparkle -->
      <path class="l-its-hover__gemini-sparkle-left" d="M4 12h4M6 10l2 2M6 14l2-2" />
      <!-- Right sparkle -->
      <path class="l-its-hover__gemini-sparkle-right" d="M16 12h4M18 10l-2 2M18 14l-2-2" />
      <!-- Bottom star -->
      <path class="l-its-hover__gemini-star-bottom" d="M12 18v4M12 18l2 2M12 18l-2 2" />
    </g>
    <!-- Central core -->
    <circle class="l-its-hover__gemini-core" cx="12" cy="12" r="4" />
    <circle class="l-its-hover__gemini-inner" cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
  </svg>
</template>
