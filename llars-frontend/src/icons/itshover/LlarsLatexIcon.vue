<template>
  <svg
    class="l-its-hover__svg l-its-hover--llars-latex"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Document body with LLARS asymmetric border-radius feel -->
    <path
      class="l-its-hover__llars-latex-doc"
      d="M6.5 3H14V8H19V19.5Q19 21 17.5 21H6.5Q5 21 5 19.5V4.5Q5 3 6.5 3Z"
    />

    <!-- Fold corner -->
    <path class="l-its-hover__llars-latex-fold" d="M14 3v4q0 1 1 1h4" />

    <!-- LaTeX integral symbol (stylized) -->
    <path
      class="l-its-hover__llars-latex-integral"
      d="M13.5 10c-0.5-0.3-1 0-1.1 0.5l-1 4c-0.1 0.5-0.6 0.8-1.1 0.5"
      stroke-width="1.8"
    />
    <!-- Integral serifs -->
    <circle cx="13.2" cy="10" r="0.6" fill="currentColor" stroke="none" />
    <circle cx="10.5" cy="15.2" r="0.6" fill="currentColor" stroke="none" />

    <!-- LLARS badge (small L) -->
    <g class="l-its-hover__llars-latex-badge">
      <path d="M7.5 11v4h2" stroke-width="1.6" />
    </g>
  </svg>
</template>
