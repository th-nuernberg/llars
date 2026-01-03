<template>
  <LCard
    class="l-card-skeleton"
    :class="{ 'l-card-skeleton--compact': compact }"
    :color="accentColor"
    :style="cardStyle"
  >
    <template #header>
      <div class="l-card-skeleton__header">
        <div class="l-card-skeleton__header-main">
          <div
            v-if="showAvatar"
            class="l-card-skeleton__block l-card-skeleton__block--circle"
            :style="blockStyle(avatarSize, avatarSize)"
          />
          <div class="l-card-skeleton__titles">
            <div
              class="l-card-skeleton__block l-card-skeleton__block--line"
              :style="blockStyle(titleWidth, titleHeight)"
            />
            <div
              v-if="showSubtitle"
              class="l-card-skeleton__block l-card-skeleton__block--line"
              :style="blockStyle(subtitleWidth, subtitleHeight)"
            />
          </div>
        </div>
        <div
          v-if="showStatus"
          class="l-card-skeleton__block l-card-skeleton__block--pill"
          :style="blockStyle(statusWidth, statusHeight)"
        />
      </div>
    </template>

    <template #default>
      <div
        v-if="descriptionLines > 0"
        class="l-card-skeleton__description"
        :style="descriptionStyle"
      >
        <div
          v-for="(width, index) in descriptionLineWidthsNormalized"
          :key="`desc-${index}`"
          class="l-card-skeleton__block l-card-skeleton__block--line"
          :style="blockStyle(width, descriptionLineHeight)"
        />
      </div>
    </template>

    <template v-if="statCount > 0" #stats>
      <div class="l-card-skeleton__stats">
        <div
          v-for="(width, index) in statWidthsNormalized"
          :key="`stat-${index}`"
          class="l-card-skeleton__block l-card-skeleton__block--line"
          :style="blockStyle(width, statHeight)"
        />
      </div>
    </template>

    <template v-if="tagCount > 0" #tags>
      <div class="l-card-skeleton__tags">
        <div
          v-for="(width, index) in tagWidthsNormalized"
          :key="`tag-${index}`"
          class="l-card-skeleton__block l-card-skeleton__block--pill"
          :style="blockStyle(width, tagHeight)"
        />
      </div>
    </template>

    <template v-if="actionsNormalized.length > 0" #actions>
      <template v-for="(action, index) in actionsNormalized" :key="`action-${index}`">
        <div
          class="l-card-skeleton__block"
          :class="action.shape === 'circle' ? 'l-card-skeleton__block--circle' : 'l-card-skeleton__block--pill'"
          :style="blockStyle(action.width, actionHeightNormalized(action))"
        />
        <v-spacer v-if="shouldInsertSpacer(index)" />
      </template>
    </template>
  </LCard>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  accentColor: {
    type: String,
    default: 'rgba(var(--v-theme-on-surface), 0.08)'
  },
  minHeight: {
    type: [Number, String],
    default: 280
  },
  compact: {
    type: Boolean,
    default: false
  },
  showAvatar: {
    type: Boolean,
    default: true
  },
  avatarSize: {
    type: [Number, String],
    default: 40
  },
  titleWidth: {
    type: [Number, String],
    default: 160
  },
  titleHeight: {
    type: [Number, String],
    default: 18
  },
  showSubtitle: {
    type: Boolean,
    default: true
  },
  subtitleWidth: {
    type: [Number, String],
    default: 110
  },
  subtitleHeight: {
    type: [Number, String],
    default: 14
  },
  showStatus: {
    type: Boolean,
    default: true
  },
  statusWidth: {
    type: [Number, String],
    default: 70
  },
  statusHeight: {
    type: [Number, String],
    default: 22
  },
  descriptionLines: {
    type: Number,
    default: 2
  },
  descriptionMinHeight: {
    type: [Number, String],
    default: 48
  },
  descriptionLineHeight: {
    type: [Number, String],
    default: 12
  },
  descriptionLineWidths: {
    type: Array,
    default: () => []
  },
  statCount: {
    type: Number,
    default: 2
  },
  statWidth: {
    type: [Number, String],
    default: 90
  },
  statHeight: {
    type: [Number, String],
    default: 12
  },
  statWidths: {
    type: Array,
    default: () => []
  },
  tagCount: {
    type: Number,
    default: 1
  },
  tagWidth: {
    type: [Number, String],
    default: 60
  },
  tagWidths: {
    type: Array,
    default: () => []
  },
  tagHeight: {
    type: [Number, String],
    default: 20
  },
  showActions: {
    type: Boolean,
    default: true
  },
  actionItems: {
    type: Array,
    default: () => []
  },
  actionSplitIndex: {
    type: Number,
    default: 1
  },
  primaryActionWidth: {
    type: [Number, String],
    default: 72
  },
  secondaryActionWidth: {
    type: [Number, String],
    default: 28
  },
  actionHeight: {
    type: [Number, String],
    default: 28
  }
})

const toCssSize = (value) => (typeof value === 'number' ? `${value}px` : value)

const blockStyle = (width, height) => ({
  width: toCssSize(width),
  height: toCssSize(height)
})

const cardStyle = computed(() => ({
  minHeight: toCssSize(props.minHeight)
}))

const descriptionStyle = computed(() => ({
  minHeight: toCssSize(props.descriptionMinHeight)
}))

const descriptionLineWidthsNormalized = computed(() => {
  if (props.descriptionLines <= 0) return []
  if (props.descriptionLineWidths.length) {
    return Array.from({ length: props.descriptionLines }, (_, index) => (
      props.descriptionLineWidths[index] ?? '100%'
    ))
  }
  return Array.from({ length: props.descriptionLines }, (_, index) => (
    index === props.descriptionLines - 1 ? '72%' : '100%'
  ))
})

const statWidthsNormalized = computed(() => {
  if (props.statCount <= 0) return []
  if (props.statWidths.length) {
    return Array.from({ length: props.statCount }, (_, index) => props.statWidths[index] ?? props.statWidth)
  }
  return Array.from({ length: props.statCount }, () => props.statWidth)
})

const tagWidthsNormalized = computed(() => {
  if (props.tagCount <= 0) return []
  if (props.tagWidths.length) {
    return Array.from({ length: props.tagCount }, (_, index) => props.tagWidths[index] ?? props.tagWidth)
  }
  return Array.from({ length: props.tagCount }, () => props.tagWidth)
})

const actionsNormalized = computed(() => {
  if (!props.showActions) return []
  if (props.actionItems.length) {
    return props.actionItems.map(item => ({
      width: item?.width ?? props.primaryActionWidth,
      height: item?.height,
      shape: item?.shape ?? 'pill'
    }))
  }
  return [
    { width: props.primaryActionWidth, height: props.actionHeight, shape: 'pill' },
    { width: props.secondaryActionWidth, height: props.actionHeight, shape: 'circle' }
  ]
})

const actionHeightNormalized = (action) => {
  if (action.shape === 'circle' && !action.height) {
    return action.width
  }
  return action.height ?? props.actionHeight
}

const shouldInsertSpacer = (index) => {
  if (!Number.isFinite(props.actionSplitIndex)) return false
  if (props.actionSplitIndex <= 0) return false
  if (props.actionSplitIndex >= actionsNormalized.value.length) return false
  return index === props.actionSplitIndex - 1
}
</script>

<style scoped>
.l-card-skeleton__block {
  background: linear-gradient(
    90deg,
    rgba(var(--v-theme-on-surface), 0.06) 25%,
    rgba(var(--v-theme-on-surface), 0.12) 37%,
    rgba(var(--v-theme-on-surface), 0.06) 63%
  );
  background-size: 400% 100%;
  border-radius: 6px;
  animation: l-card-skeleton-shimmer 1.2s ease-in-out infinite;
}

.l-card-skeleton__block--circle {
  border-radius: 50%;
}

.l-card-skeleton__block--pill {
  border-radius: 999px;
}

@keyframes l-card-skeleton-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: 0 0; }
}

.l-card-skeleton__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.l-card-skeleton__header-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.l-card-skeleton__titles {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.l-card-skeleton__description {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.l-card-skeleton__stats {
  display: flex;
  align-items: center;
  gap: 16px;
}

.l-card-skeleton__tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
</style>
