<template>
  <svg
    class="l-its-hover__svg l-its-hover--ollama"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Ollama - Minimalist llama profile silhouette -->
    <!-- Neck and body curve -->
    <path
      class="l-its-hover__ollama-body"
      d="M8 21c0-4 0-8 2-11c1-2 2-3 2-5"
    />
    <!-- Head -->
    <circle class="l-its-hover__ollama-head" cx="12" cy="4" r="2.5" />
    <!-- Left ear -->
    <path class="l-its-hover__ollama-ear l-its-hover__ollama-ear--left" d="M10 3L8 1" />
    <!-- Right ear -->
    <path class="l-its-hover__ollama-ear l-its-hover__ollama-ear--right" d="M14 3l2-2" />
    <!-- Eye -->
    <circle class="l-its-hover__ollama-eye" cx="11.5" cy="4" r="0.7" fill="currentColor" stroke="none" />
    <!-- Back/wool -->
    <path
      class="l-its-hover__ollama-back"
      d="M12 7c3 2 5 5 5 9c0 2 0 4-1 5"
    />
    <!-- Legs -->
    <g class="l-its-hover__ollama-legs">
      <path d="M10 21v-3" />
      <path d="M14 21v-4" />
    </g>
  </svg>
</template>

<style>
.l-its-hover__ollama-ear {
  transform-origin: bottom;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__ollama-head {
  transition: transform 0.3s ease;
}

.l-its-hover__ollama-eye {
  transition: transform 0.2s ease;
}

:is(.v-icon:hover, .quick-card:hover .v-icon) .l-its-hover--ollama .l-its-hover__ollama-ear--left {
  transform: rotate(-15deg);
}

:is(.v-icon:hover, .quick-card:hover .v-icon) .l-its-hover--ollama .l-its-hover__ollama-ear--right {
  transform: rotate(15deg);
}

:is(.v-icon:hover, .quick-card:hover .v-icon) .l-its-hover--ollama .l-its-hover__ollama-head {
  transform: translateY(-1px);
}

:is(.v-icon:hover, .quick-card:hover .v-icon) .l-its-hover--ollama .l-its-hover__ollama-eye {
  transform: scale(1.3);
}
</style>
