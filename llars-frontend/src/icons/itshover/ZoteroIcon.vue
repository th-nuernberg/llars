<template>
  <svg
    class="l-its-hover__svg l-its-hover--zotero"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Zotero "Z" shape - the iconic logo -->
    <path
      class="l-its-hover__zotero-z"
      d="M6 5h12M18 5L6 19M6 19h12"
    />
    <!-- Small book/reference indicator -->
    <path
      class="l-its-hover__zotero-book"
      d="M3 7v10M3 7c0 0 1.5-1 3-1M3 17c0 0 1.5 1 3 1"
      stroke-width="1.25"
      opacity="0.6"
    />
  </svg>
</template>

<style>
/* Zotero icon - static, no hover animation */
.l-its-hover--zotero {
  /* Zotero brand color */
  --zotero-color: #CC2936;
}

.l-its-hover__zotero-z {
  stroke: var(--zotero-color);
  stroke-width: 2;
  transition: stroke-width 0.2s ease;
}

.l-its-hover__zotero-book {
  stroke: currentColor;
  transition: opacity 0.2s ease;
}

/* Subtle hover effect */
:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--zotero .l-its-hover__zotero-z {
  stroke-width: 2.25;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--zotero .l-its-hover__zotero-book {
  opacity: 0.8;
}
</style>
