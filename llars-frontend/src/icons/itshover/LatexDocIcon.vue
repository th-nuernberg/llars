<template>
  <svg
    class="l-its-hover__svg l-its-hover--latex-doc"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Document body (same structure as latex-ai) -->
    <path class="l-its-hover__latex-doc-file" d="M6 3h7.5" />
    <path class="l-its-hover__latex-doc-file" d="M18 7.0v13.5H6V3" />

    <!-- Fold corner - 4x4, aligned with page edges -->
    <path class="l-its-hover__latex-doc-crease" d="M14.5 3.5L17.5 6.5" />
    <path class="l-its-hover__latex-doc-fold" d="M14 3v3q0 1 1 1h3" />

    <!-- LaTeX formula (integral symbol) - smaller and more compact -->
    <g class="l-its-hover__latex-doc-formula">
      <path d="M10 10.5c-0.6 0-0.9 0.3-0.9 0.9v3c0 0.6 0.3 0.9 0.9 0.9" />
      <path d="M9.4 12.5h1.8" />
    </g>

    <!-- dx notation - smaller -->
    <g class="l-its-hover__latex-doc-dx">
      <path d="M12 11.5v3" />
      <path d="M13.2 11.5l-0.9 1.5l0.9 1.5" />
    </g>
  </svg>
</template>
