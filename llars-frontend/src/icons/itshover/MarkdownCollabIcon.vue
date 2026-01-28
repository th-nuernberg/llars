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
    <!-- Document with folded corner (DEFAULT - visible) -->
    <path
      class="l-its-hover__markdown-file-folded"
      d="M6.5 3H14V8H19V19.5Q19 21 17.5 21H6.5Q5 21 5 19.5V4.5Q5 3 6.5 3Z"
    />

    <!-- Document with rounded corner (HOVER - hidden by default) -->
    <path
      class="l-its-hover__markdown-file-flat"
      d="M6.5 3H17.5Q19 3 19 4.5V19.5Q19 21 17.5 21H6.5Q5 21 5 19.5V4.5Q5 3 6.5 3Z"
    />

    <!-- Fold corner - animated dog-ear -->
    <path class="l-its-hover__markdown-crease" d="M14.5 3.5L18.5 7.5" />
    <path class="l-its-hover__markdown-fold" d="M14 3v4q0 1 1 1h4" />

    <!-- Markdown hash symbol (#) -->
    <path class="l-its-hover__markdown-hash" d="M9.5 10v5M11.5 10v5M8 11.5h5M8 13.5h5" />
  </svg>
</template>
