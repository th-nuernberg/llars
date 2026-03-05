<template>
  <v-chip
    :size="size"
    variant="flat"
    :style="{ backgroundColor: color + '33', color: color, borderRadius: '6px 2px 6px 2px' }"
  >
    <v-icon start size="14">mdi-trophy-outline</v-icon>
    {{ displayLabel }}
  </v-chip>
</template>

<script setup>
import { computed } from 'vue'
import { CORE_RANKINGS, getRankingColor } from '../config/conferenceConfig'

const props = defineProps({
  ranking: { type: String, default: 'Unranked' },
  size: { type: String, default: 'small' },
})

const color = computed(() => getRankingColor(props.ranking))
const displayLabel = computed(() => CORE_RANKINGS.find(r => r.value === props.ranking)?.label || props.ranking)
</script>
