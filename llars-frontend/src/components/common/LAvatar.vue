<template>
  <div
    class="l-avatar"
    :class="[
      `l-avatar--${size}`,
      { 'l-avatar--clickable': clickable }
    ]"
    :style="avatarStyle"
  >
    <img
      v-if="avatarUrl"
      :src="avatarUrl"
      :alt="alt || username"
      class="l-avatar__image"
      @error="handleImageError"
    />
    <span v-else class="l-avatar__fallback">
      {{ fallbackInitial }}
    </span>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  /**
   * The seed for generating a consistent avatar (from DB)
   * If not provided, falls back to username-based avatar
   */
  seed: {
    type: String,
    default: null
  },
  /**
   * Username - used for fallback initial and alt text
   */
  username: {
    type: String,
    default: ''
  },
  /**
   * Avatar size
   */
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['xs', 'sm', 'md', 'lg', 'xl'].includes(v)
  },
  /**
   * Avatar style/type from DiceBear
   * Options: bottts, shapes, thumbs, fun-emoji, lorelei-neutral, identicon, rings
   */
  variant: {
    type: String,
    default: 'bottts-neutral'
  },
  /**
   * Background color (optional - uses LLARS colors by default)
   */
  backgroundColor: {
    type: String,
    default: null
  },
  /**
   * Alt text for the image
   */
  alt: {
    type: String,
    default: null
  },
  /**
   * Whether the avatar is clickable
   */
  clickable: {
    type: Boolean,
    default: false
  }
});

const imageError = ref(false);

// Size map in pixels
const sizeMap = {
  xs: 24,
  sm: 32,
  md: 40,
  lg: 56,
  xl: 80
};

// LLARS color palette for backgrounds (pastel colors)
const llarsColors = [
  'b0ca97', // primary - sage green
  '98d4bb', // success - soft mint
  'a8c5e2', // info - soft blue
  'e8c87a', // warning - soft gold
  '88c4c8', // accent - soft teal
  'D1BC8A', // secondary - golden beige
  'e8a087', // danger - soft coral
  'c5b4e3', // purple - soft lavender
  'f0b6c2', // pink - soft rose
];

// Generate a consistent color index from seed/username
const colorFromSeed = computed(() => {
  const str = props.seed || props.username || 'default';
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % llarsColors.length;
  return llarsColors[index];
});

// Build the DiceBear avatar URL
const avatarUrl = computed(() => {
  if (imageError.value) return null;

  const seedValue = props.seed || props.username || 'anonymous';
  const size = sizeMap[props.size] * 2; // 2x for retina
  const bgColor = props.backgroundColor || colorFromSeed.value;

  // DiceBear API v7
  return `https://api.dicebear.com/7.x/${props.variant}/svg?seed=${encodeURIComponent(seedValue)}&size=${size}&backgroundColor=${bgColor}`;
});

// Fallback initial from username
const fallbackInitial = computed(() => {
  if (!props.username) return '?';
  return props.username.charAt(0).toUpperCase();
});

// Avatar container style
const avatarStyle = computed(() => {
  const size = sizeMap[props.size];
  const bgColor = props.backgroundColor || `#${colorFromSeed.value}`;

  return {
    width: `${size}px`,
    height: `${size}px`,
    backgroundColor: imageError.value ? bgColor : 'transparent'
  };
});

const handleImageError = () => {
  imageError.value = true;
};
</script>

<style scoped>
.l-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px 4px 12px 4px; /* LLARS asymmetric style */
  overflow: hidden;
  flex-shrink: 0;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.l-avatar--clickable {
  cursor: pointer;
}

.l-avatar--clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Sizes */
.l-avatar--xs {
  border-radius: 6px 2px 6px 2px;
}

.l-avatar--sm {
  border-radius: 8px 3px 8px 3px;
}

.l-avatar--md {
  border-radius: 12px 4px 12px 4px;
}

.l-avatar--lg {
  border-radius: 14px 5px 14px 5px;
}

.l-avatar--xl {
  border-radius: 16px 6px 16px 6px;
}

.l-avatar__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.l-avatar__fallback {
  font-weight: 600;
  color: white;
  text-transform: uppercase;
  user-select: none;
}

/* Fallback text sizes */
.l-avatar--xs .l-avatar__fallback {
  font-size: 10px;
}

.l-avatar--sm .l-avatar__fallback {
  font-size: 12px;
}

.l-avatar--md .l-avatar__fallback {
  font-size: 14px;
}

.l-avatar--lg .l-avatar__fallback {
  font-size: 18px;
}

.l-avatar--xl .l-avatar__fallback {
  font-size: 24px;
}
</style>
