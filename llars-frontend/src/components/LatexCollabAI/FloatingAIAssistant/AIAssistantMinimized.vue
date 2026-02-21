<template>
  <div class="assistant-minimized">
    <v-btn
      class="minimized-btn"
      :title="$t('floatingAi.openAssistant')"
      @click="$emit('maximize')"
    >
      <v-badge
        v-if="unreadCount > 0"
        :content="unreadCount"
        color="error"
        floating
      >
        <LIcon color="white" class="mr-2">mdi-robot-happy</LIcon>
      </v-badge>
      <LIcon v-else color="white" class="mr-2">mdi-robot-happy</LIcon>
      <span class="btn-label">{{ $t('floatingAi.title') }}</span>
    </v-btn>
  </div>
</template>

<script setup>
defineProps({
  unreadCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['maximize'])
</script>

<style scoped>
.assistant-minimized {
  position: fixed;
  top: 72px;
  right: 12px;
  z-index: 100;
  pointer-events: auto;
}

.minimized-btn {
  background: linear-gradient(135deg, #88c4c8 0%, #b0ca97 100%);
  border-radius: 12px 4px 12px 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  color: white;
  font-weight: 600;
  font-size: 13px;
  padding: 8px 16px;
  height: auto;
  min-height: 36px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.minimized-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.btn-label {
  letter-spacing: 0.3px;
}
</style>
