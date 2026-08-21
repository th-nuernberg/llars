<template>
  <!--
    Ticket icon — used for invitation / referral codes (auth.inviteCode).
    Visual is a classic admission ticket with a perforation line and a
    small check mark on the right half, which mirrors the
    ``mdi-ticket-confirmation`` semantics this icon replaces in
    Register.vue.
  -->
  <svg
    class="l-its-hover__svg l-its-hover--ticket"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Ticket body -->
    <rect x="3" y="6" width="18" height="12" rx="2" />
    <!-- Perforation: vertical dashed line at one-third -->
    <path d="M9 6v12" stroke-dasharray="2 2" />
    <!-- Confirmation tick on the right portion -->
    <path d="M13.5 12.2l1.4 1.4L17.5 11" />
  </svg>
</template>
