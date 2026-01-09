<template>
  <svg
    class="l-its-hover__svg l-its-hover--markdown-collab"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Document body (same structure as latex-ai for consistent fold) -->
    <path class="l-its-hover__markdown-file" d="M6 3h7.5" />
    <path class="l-its-hover__markdown-file" d="M18 7.5v13.5H6V3" />

    <!-- Fold corner - 4x4, aligned with page edges -->
    <path class="l-its-hover__markdown-crease" d="M14.5 3.5L17.5 6.5" />
    <path class="l-its-hover__markdown-fold" d="M14 3v3q0 1 1 1h3" />

    <!-- Markdown hash symbol (#) - smaller and more compact -->
    <path class="l-its-hover__markdown-hash" d="M9.5 10.5v5M11.5 10.5v5M8 12h5M8 14h5" />
  </svg>
</template>
