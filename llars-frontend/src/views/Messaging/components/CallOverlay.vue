<template>
  <v-dialog
    v-if="incomingCall"
    :model-value="true"
    max-width="380"
    persistent
  >
    <v-card class="text-center pa-6">
      <v-icon size="48" color="primary" class="mb-3">
        {{ incomingCall.call_type === 'video' ? 'mdi-video' : 'mdi-phone' }}
      </v-icon>
      <h3 class="mb-1">{{ $t(`messaging.call.${incomingCall.call_type}`) }}</h3>
      <p class="text-body-2 mb-4" style="opacity: 0.7">
        {{ incomingCall.initiated_by }}
      </p>
      <div class="d-flex justify-center gap-4">
        <v-btn
          icon
          color="error"
          size="large"
          @click="$emit('decline')"
        >
          <v-icon>mdi-phone-hangup</v-icon>
        </v-btn>
        <v-btn
          icon
          color="success"
          size="large"
          @click="$emit('accept')"
        >
          <v-icon>mdi-phone</v-icon>
        </v-btn>
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup>
defineProps({
  incomingCall: { type: Object, default: null },
})

defineEmits(['accept', 'decline'])
</script>
