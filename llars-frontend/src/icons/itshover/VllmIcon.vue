<template>
  <svg
    class="l-its-hover__svg l-its-hover--vllm"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- vLLM-inspired V shape with speed lines -->
    <path class="l-its-hover__vllm-v" d="M4 4l8 16l8-16" />
    <!-- Speed lines -->
    <g class="l-its-hover__vllm-speed">
      <line x1="2" y1="8" x2="6" y2="8" />
      <line x1="1" y1="12" x2="7" y2="12" />
      <line x1="2" y1="16" x2="6" y2="16" />
    </g>
    <!-- Neural nodes -->
    <g class="l-its-hover__vllm-nodes">
      <circle cx="12" cy="10" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="8" cy="6" r="1" fill="currentColor" stroke="none" />
      <circle cx="16" cy="6" r="1" fill="currentColor" stroke="none" />
    </g>
  </svg>
</template>
