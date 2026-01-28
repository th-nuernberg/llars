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
    <!-- Document body: rounded corners -->
    <path
      class="l-its-hover__latex-file"
      d="M6.5 3H17.5Q19 3 19 4.5V19.5Q19 21 17.5 21H6.5Q5 21 5 19.5V4.5Q5 3 6.5 3Z"
    />

    <!-- Corner indent lines (fade on hover to show flat document) -->
    <path class="l-its-hover__latex-corner" d="M14 3V8H19" />

    <!-- Fold corner - animated dog-ear -->
    <path class="l-its-hover__latex-crease" d="M14.5 3.5L18.5 7.5" />
    <path class="l-its-hover__latex-fold" d="M14 3v4q0 1 1 1h4" />

    <!-- Sigma symbol -->
    <path class="l-its-hover__latex-sigma" d="M9.5 10h2.5l-1.8 2l1.8 2H9.5" />

    <!-- Text lines -->
    <path class="l-its-hover__latex-eq" d="M9.5 16h3" />
    <path class="l-its-hover__latex-eq" d="M9.5 17.5h2" />

    <!-- AI Sparkles -->
    <g class="l-its-hover__latex-ai-sparkles">
      <path class="l-its-hover__latex-ai-sparkle l-its-hover__latex-ai-sparkle--one" d="M21 12v1.5M20.25 12.75h1.5" />
      <path class="l-its-hover__latex-ai-sparkle l-its-hover__latex-ai-sparkle--two" d="M22.5 15v1M22 15.5h1" />
    </g>
  </svg>
</template>
