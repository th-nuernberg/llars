<template>
  <!--
    LLARS "Span zusammenführen" icon.

    Visual metaphor: two units becoming one. The mirror image of
    SpanSplitIcon — the same two halves, but with arrows pushing them
    together against a single seam instead of a cut standing between them.
    Read side by side the pair should be unmistakable as opposites.

    Stroke-only, 1.5 px, matching the rest of the LLARS line-icon set.
  -->
  <svg
    class="l-its-hover__svg l-its-hover--span-merge"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Left half, pushed inward -->
    <rect x="1.5" y="8.5" width="7" height="7" rx="1.5" />
    <!-- Right half, pushed inward -->
    <rect x="15.5" y="8.5" width="7" height="7" rx="1.5" />
    <!-- The seam they close onto -->
    <line x1="12" y1="6.5" x2="12" y2="17.5" />
    <!-- Arrows pressing the halves together -->
    <path d="M9.4 12 H11.2" />
    <path d="M10 10.8 L11.2 12 L10 13.2" />
    <path d="M14.6 12 H12.8" />
    <path d="M14 10.8 L12.8 12 L14 13.2" />
  </svg>
</template>
