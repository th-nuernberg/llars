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
    <!-- Document body with rounded corners (like BatchGeneration) -->
    <rect class="l-its-hover__markdown-file" x="5" y="3" width="14" height="18" rx="1.5" />

    <!-- Fold corner overlay - covers top-right corner -->
    <path class="l-its-hover__markdown-crease" d="M14.5 3.5L18.5 7.5" />
    <path class="l-its-hover__markdown-fold" d="M14 3v4q0 1 1 1h4" />

    <!-- Markdown hash symbol (#) -->
    <path class="l-its-hover__markdown-hash" d="M9.5 10.5v5M11.5 10.5v5M8 12h5M8 14h5" />

    <!-- Collab users indicator -->
    <g class="l-its-hover__markdown-users">
      <circle cx="16" cy="17" r="1.5" />
      <circle cx="18" cy="15" r="1.5" />
    </g>
  </svg>
</template>
