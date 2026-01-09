<template>
  <svg
    class="l-its-hover__svg l-its-hover--system-theme"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Monitor/device frame -->
    <rect class="l-its-hover__system-monitor" x="3" y="4" width="18" height="12" rx="2" />
    <path class="l-its-hover__system-stand" d="M8 20h8M12 16v4" />

    <!-- Split sun/moon inside monitor -->
    <g class="l-its-hover__system-content">
      <!-- Left side: mini sun (light) -->
      <g class="l-its-hover__system-sun">
        <circle cx="8" cy="10" r="1.5" />
        <path d="M8 6.5v1M8 12.5v1M5.5 10h1M9.5 10h1" />
      </g>

      <!-- Divider -->
      <path class="l-its-hover__system-divider" d="M12 7v6" stroke-dasharray="1.5 1.5" />

      <!-- Right side: mini moon (dark) -->
      <path class="l-its-hover__system-moon" d="M17.5 10a3 3 0 1 1-3-3 2.2 2.2 0 0 0 3 3z" />
    </g>
  </svg>
</template>
