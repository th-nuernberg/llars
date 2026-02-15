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
import { computed, ref, watch } from 'vue';
import { LLARS_COLORS } from '@/constants/colors';

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
   * Custom avatar image URL (optional)
   */
  src: {
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
   * Options: initials (human default), bottts-neutral (for AI/bots only), shapes, thumbs, fun-emoji
   */
  variant: {
    type: String,
    default: 'initials'
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
  },
  /**
   * Whether to use LLARS gradient background (for fallback/initials)
   */
  gradient: {
    type: Boolean,
    default: true
  }
});

const customFailed = ref(false);
const generatedFailed = ref(false);

// Size map in pixels
const sizeMap = {
  xs: 24,
  sm: 32,
  md: 40,
  lg: 56,
  xl: 80
};

// Use global LLARS color palette for backgrounds
const llarsColors = LLARS_COLORS;

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

// Keep initials tied to username so letter rendering stays consistent.
// Seed still influences colors/background via separate computations.
const generatedSeedValue = computed(() => {
  if (props.variant === 'initials' && props.username) {
    return props.username;
  }
  return props.seed || props.username || 'anonymous';
});

// Build the DiceBear avatar URL
const generatedAvatarUrl = computed(() => {
  const seedValue = generatedSeedValue.value;
  const size = sizeMap[props.size] * 2; // 2x for retina

  // Use transparent background when gradient is enabled, otherwise use solid color
  const bgColor = props.gradient ? 'transparent' : (props.backgroundColor || colorFromSeed.value);

  // DiceBear API v7
  return `https://api.dicebear.com/7.x/${props.variant}/svg?seed=${encodeURIComponent(seedValue)}&size=${size}&backgroundColor=${bgColor}`;
});

const avatarUrl = computed(() => {
  if (props.src && !customFailed.value) return props.src;
  if (!generatedFailed.value) return generatedAvatarUrl.value;
  return null;
});

// Fallback initial from username
const fallbackInitial = computed(() => {
  if (!props.username) return '?';
  return props.username.charAt(0).toUpperCase();
});

// Generate gradient colors based on seed (two colors for gradient)
const gradientColors = computed(() => {
  const str = props.seed || props.username || 'default';
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index1 = Math.abs(hash) % llarsColors.length;
  const index2 = Math.abs(hash * 7) % llarsColors.length;
  return [llarsColors[index1], llarsColors[index2 === index1 ? (index2 + 1) % llarsColors.length : index2]];
});

// Check if using custom uploaded image (not DiceBear generated)
const hasCustomImage = computed(() => {
  return props.src && !customFailed.value;
});

// Avatar container style
const avatarStyle = computed(() => {
  const size = sizeMap[props.size];

  // If custom uploaded image, transparent background
  if (hasCustomImage.value) {
    return {
      width: `${size}px`,
      height: `${size}px`,
      background: 'transparent'
    };
  }

  // For DiceBear generated or fallback: use gradient or solid color
  if (props.gradient) {
    const [color1, color2] = gradientColors.value;
    return {
      width: `${size}px`,
      height: `${size}px`,
      background: `linear-gradient(135deg, #${color1} 0%, #${color2} 100%)`
    };
  }

  // Solid color
  const bgColor = props.backgroundColor || `#${colorFromSeed.value}`;
  return {
    width: `${size}px`,
    height: `${size}px`,
    background: bgColor
  };
});

const handleImageError = () => {
  if (props.src && !customFailed.value) {
    customFailed.value = true;
    return;
  }
  generatedFailed.value = true;
};

watch(
  () => props.src,
  () => {
    customFailed.value = false;
    generatedFailed.value = false;
  }
);

watch(
  () => [props.seed, props.username, props.variant, props.size, props.backgroundColor],
  () => {
    generatedFailed.value = false;
  }
);
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
