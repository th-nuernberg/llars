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
          <v-skeleton-loader
            v-if="showAvatar"
            type="avatar"
            :width="avatarSize"
            :height="avatarSize"
          />
          <div class="l-card-skeleton__titles">
            <v-skeleton-loader type="text" :width="titleWidth" :height="titleHeight" />
            <v-skeleton-loader
              v-if="showSubtitle"
              type="text"
              :width="subtitleWidth"
              :height="subtitleHeight"
            />
          </div>
        </div>
        <v-skeleton-loader
          v-if="showStatus"
          type="chip"
          :width="statusWidth"
          :height="statusHeight"
        />
      </div>
    </template>

    <template #default>
      <div
        v-if="descriptionLines > 0"
        class="l-card-skeleton__description"
        :style="descriptionStyle"
      >
        <v-skeleton-loader :type="`paragraph@${descriptionLines}`" />
      </div>
    </template>

    <template v-if="statCount > 0" #stats>
      <div class="l-card-skeleton__stats">
        <v-skeleton-loader
          v-for="(width, index) in statWidthsNormalized"
          :key="`stat-${index}`"
          type="text"
          :width="width"
        />
      </div>
    </template>

    <template v-if="tagCount > 0" #tags>
      <div class="l-card-skeleton__tags">
        <v-skeleton-loader
          v-for="(width, index) in tagWidthsNormalized"
          :key="`tag-${index}`"
          type="chip"
          :width="width"
          :height="tagHeight"
        />
      </div>
    </template>

    <template v-if="showActions" #actions>
      <v-skeleton-loader type="button" :width="primaryActionWidth" :height="actionHeight" />
      <v-spacer />
      <v-skeleton-loader type="button" :width="secondaryActionWidth" :height="actionHeight" />
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
  statCount: {
    type: Number,
    default: 2
  },
  statWidth: {
    type: [Number, String],
    default: 90
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

const cardStyle = computed(() => ({
  minHeight: toCssSize(props.minHeight)
}))

const descriptionStyle = computed(() => ({
  minHeight: toCssSize(props.descriptionMinHeight)
}))

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
</script>

<style scoped>
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
