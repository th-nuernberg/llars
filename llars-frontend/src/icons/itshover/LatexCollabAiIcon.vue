<template>
  <svg
    class="l-its-hover__svg l-its-hover--latex-ai"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path class="l-its-hover__latex-file" d="M6 3h7.5" />
    <path class="l-its-hover__latex-file" d="M18 7.5v13.5H6V3" />
    <!-- Fold corner - 4x4, aligned with page edges -->
    <path class="l-its-hover__latex-crease" d="M14.5 3.5L17.5 6.5" />
    <path class="l-its-hover__latex-fold" d="M14 3v3q0 1 1 1h3" />
    <!-- Sigma symbol - smaller and more compact -->
    <path class="l-its-hover__latex-sigma" d="M9.5 10h2.5l-1.8 2l1.8 2H9.5" />
    <!-- Text lines - smaller -->
    <path class="l-its-hover__latex-eq" d="M9.5 16h3" />
    <path class="l-its-hover__latex-eq" d="M9.5 17.5h2" />
    <!-- AI Sparkles (positioned away from fold corner) -->
    <g class="l-its-hover__latex-ai-sparkles">
      <path class="l-its-hover__latex-ai-sparkle l-its-hover__latex-ai-sparkle--one" d="M21 12v1.5M20.25 12.75h1.5" />
      <path class="l-its-hover__latex-ai-sparkle l-its-hover__latex-ai-sparkle--two" d="M22.5 15v1M22 15.5h1" />
    </g>
  </svg>
</template>
