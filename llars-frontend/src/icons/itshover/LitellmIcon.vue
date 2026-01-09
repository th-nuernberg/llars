<template>
  <svg
    class="l-its-hover__svg l-its-hover--litellm"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- LiteLLM-inspired gateway/proxy icon -->
    <!-- Gateway frame -->
    <rect class="l-its-hover__litellm-gate" x="8" y="3" width="8" height="18" rx="1" />
    <!-- Input arrows -->
    <g class="l-its-hover__litellm-inputs">
      <path d="M2 7h4l2 2" />
      <path d="M2 12h6" />
      <path d="M2 17h4l2-2" />
    </g>
    <!-- Output arrows -->
    <g class="l-its-hover__litellm-outputs">
      <path d="M16 9l2-2h4" />
      <path d="M16 12h6" />
      <path d="M16 15l2 2h4" />
    </g>
    <!-- Central processing indicator -->
    <g class="l-its-hover__litellm-process">
      <circle cx="12" cy="9" r="1" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
      <circle cx="12" cy="15" r="1" fill="currentColor" stroke="none" />
    </g>
  </svg>
</template>
