<template>
  <div v-if="hasPermission('feature:communication:ai')" class="d-flex align-center gap-2">
    <LSwitch
      v-model="aiEnabled"
      :label="$t('messaging.aiAccess')"
      :loading="isProcessing"
      @update:model-value="toggleAI"
    />
    <LTooltip :text="$t('messaging.aiAccessTooltip')">
      <v-icon size="16" class="ml-1">mdi-information-outline</v-icon>
    </LTooltip>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usePermissions } from '@/composables/usePermissions'
import { useEncryption } from '../composables/useEncryption'

const { hasPermission } = usePermissions()

const props = defineProps({
  conversationId: { type: Number, required: true },
  initialValue: { type: Boolean, default: false },
})

const { grantAIAccess, revokeAIAccess } = useEncryption()

const aiEnabled = ref(props.initialValue)
const isProcessing = ref(false)

const toggleAI = async (value) => {
  isProcessing.value = true
  try {
    if (value) {
      // Grant AI access with a placeholder key
      await grantAIAccess(props.conversationId, 'ai-delegated-key')
    } else {
      await revokeAIAccess(props.conversationId)
    }
  } catch (err) {
    console.error('[AI Grant] Toggle failed:', err)
    aiEnabled.value = !value // revert
  } finally {
    isProcessing.value = false
  }
}
</script>
