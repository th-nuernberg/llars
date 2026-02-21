<template>
  <svg
    class="l-its-hover__svg l-its-hover--admin-dashboard"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Monitor/Screen -->
    <rect class="l-its-hover__admin-screen" x="2" y="3" width="20" height="14" rx="2" />

    <!-- Screen stand -->
    <path class="l-its-hover__admin-stand" d="M8 21h8M12 17v4" />

    <!-- Dashboard content: Speedometer/Gauge - compact -->
    <g class="l-its-hover__admin-gauge">
      <path d="M7.5 13a3 3 0 0 1 6 0" />
      <path class="l-its-hover__admin-needle" d="M10.5 13l-1.3-2" />
      <circle cx="10.5" cy="13" r="0.7" fill="currentColor" stroke="none" />
    </g>

    <!-- Status indicators -->
    <g class="l-its-hover__admin-status">
      <circle class="l-its-hover__admin-dot l-its-hover__admin-dot--one" cx="6" cy="6" r="1" fill="currentColor" stroke="none" />
      <circle class="l-its-hover__admin-dot l-its-hover__admin-dot--two" cx="9" cy="6" r="1" fill="currentColor" stroke="none" />
      <circle class="l-its-hover__admin-dot l-its-hover__admin-dot--three" cx="12" cy="6" r="1" fill="currentColor" stroke="none" />
    </g>

    <!-- Mini bars on right side - compact -->
    <g class="l-its-hover__admin-bars">
      <path d="M17 9v4" />
      <path d="M19 10v3" />
    </g>
  </svg>
</template>
