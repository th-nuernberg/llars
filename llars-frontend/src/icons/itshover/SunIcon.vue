<template>
  <svg
    class="l-its-hover__svg l-its-hover--sun"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Sun center -->
    <circle class="l-its-hover__sun-center" cx="12" cy="12" r="4" />

    <!-- Sun rays - rotate on hover -->
    <g class="l-its-hover__sun-rays">
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="M4.93 4.93l1.41 1.41" />
      <path d="M17.66 17.66l1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="M6.34 17.66l-1.41 1.41" />
      <path d="M19.07 4.93l-1.41 1.41" />
    </g>
  </svg>
</template>
