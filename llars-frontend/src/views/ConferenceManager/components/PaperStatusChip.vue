<template>
  <v-chip
    :size="size"
    variant="flat"
    :style="{ backgroundColor: config.color + '33', color: config.color, borderRadius: '6px 2px 6px 2px' }"
  >
    <v-icon start size="14">{{ config.icon }}</v-icon>
    {{ t(config.labelKey) }}
  </v-chip>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { getStatusConfig } from '../config/conferenceConfig'

const { t } = useI18n()

const props = defineProps({
  status: { type: String, default: 'planning' },
  size: { type: String, default: 'small' },
})

const config = computed(() => getStatusConfig(props.status))
</script>
