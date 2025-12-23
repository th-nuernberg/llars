<template>
  <span class="l-tooltip-wrapper" :class="{ 'l-tooltip-wrapper--inline': inline }">
    <slot />
    <v-tooltip
      v-if="text"
      activator="parent"
      :location="location"
      :open-delay="openDelay"
      :close-delay="closeDelay"
    >
      <template v-if="$slots.content" #default>
        <slot name="content" />
      </template>
      <template v-else>
        {{ text }}
      </template>
    </v-tooltip>
  </span>
</template>

<script setup>
/**
 * LTooltip - LLARS Global Tooltip Wrapper Component
 *
 * Wraps any element to add a tooltip on hover.
 * Uses Vuetify's v-tooltip under the hood with LLARS styling.
 *
 * Usage:
 *   <LTooltip text="This is a helpful hint">
 *     <v-icon>mdi-help-circle</v-icon>
 *   </LTooltip>
 *
 *   <LTooltip text="Click to save" location="top">
 *     <LBtn variant="primary">Save</LBtn>
 *   </LTooltip>
 *
 *   <!-- With custom content -->
 *   <LTooltip>
 *     <v-chip>Status</v-chip>
 *     <template #content>
 *       <div><strong>Details:</strong></div>
 *       <ul><li>Item 1</li><li>Item 2</li></ul>
 *     </template>
 *   </LTooltip>
 */
defineProps({
  /**
   * Tooltip text content
   */
  text: {
    type: String,
    default: ''
  },

  /**
   * Tooltip position
   */
  location: {
    type: String,
    default: 'bottom',
    validator: (v) => ['top', 'bottom', 'start', 'end', 'left', 'right'].includes(v)
  },

  /**
   * Delay before showing tooltip (ms)
   */
  openDelay: {
    type: Number,
    default: 300
  },

  /**
   * Delay before hiding tooltip (ms)
   */
  closeDelay: {
    type: Number,
    default: 0
  },

  /**
   * Use inline display (span) vs block-like (inline-block)
   */
  inline: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.l-tooltip-wrapper {
  display: inline-block;
}

.l-tooltip-wrapper--inline {
  display: inline;
}
</style>
