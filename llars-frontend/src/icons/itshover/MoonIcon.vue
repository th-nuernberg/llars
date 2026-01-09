<template>
  <svg
    class="l-its-hover__svg l-its-hover--moon"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Moon crescent -->
    <path
      class="l-its-hover__moon-crescent"
      d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
    />

    <!-- Stars that twinkle on hover -->
    <g class="l-its-hover__moon-stars">
      <path class="l-its-hover__moon-star l-its-hover__moon-star--one" d="M17 4v2M16 5h2" />
      <path class="l-its-hover__moon-star l-its-hover__moon-star--two" d="M20 9v1.5M19.25 9.75h1.5" />
      <path class="l-its-hover__moon-star l-its-hover__moon-star--three" d="M14 7v1M13.5 7.5h1" />
    </g>
  </svg>
</template>
