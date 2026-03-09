<template>
  <svg
    class="l-its-hover__svg l-its-hover--reply"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Arrow pointing left (reply direction) -->
    <path
      class="l-its-hover__reply-arrow"
      d="M9 17l-5-5 5-5"
    />
    <!-- Curved path from arrow to right -->
    <path
      class="l-its-hover__reply-curve"
      d="M4 12h11a4 4 0 0 1 4 4v1"
    />
  </svg>
</template>

<style>
/* Reply icon - hover animation */
.l-its-hover__reply-arrow,
.l-its-hover__reply-curve {
  transition: transform 0.25s ease;
}

.l-its-hover__reply-arrow {
  transform-origin: 9px 12px;
}

.l-its-hover__reply-curve {
  transform-origin: 12px 12px;
}

/* Hover: arrow nudges left, curve follows */
:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--reply .l-its-hover__reply-arrow {
  transform: translateX(-2px);
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--reply .l-its-hover__reply-curve {
  transform: translateX(-1px);
}
</style>
