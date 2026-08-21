<template>
  <svg
    class="l-its-hover__svg l-its-hover--pdf-download"
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
      class="l-its-hover__pdf-download-doc"
      d="M6.5 3H14V7H18V19.5Q18 21 16.5 21H6.5Q5 21 5 19.5V4.5Q5 3 6.5 3Z"
    />

    <!-- Fold corner -->
    <path class="l-its-hover__pdf-download-fold" d="M14 3v3q0 1 1 1h3" />

    <!-- PDF label -->
    <text
      x="11.5"
      y="12.5"
      text-anchor="middle"
      font-size="5"
      font-weight="700"
      font-family="system-ui, sans-serif"
      fill="currentColor"
      stroke="none"
      letter-spacing="0.3"
    >PDF</text>

    <!-- Download arrow (bottom-right badge) -->
    <g class="l-its-hover__pdf-download-arrow">
      <circle cx="19" cy="18" r="4.5" fill="rgb(var(--v-theme-surface))" stroke="currentColor" stroke-width="1.2" />
      <path d="M19 15.8v3.8" stroke-width="1.4" />
      <path d="M17.3 18l1.7 1.6 1.7-1.6" stroke-width="1.4" />
    </g>
  </svg>
</template>
