<template>
  <div class="likert-scale-container">
    <span class="likert-label-text">Gut</span>
    <div class="likert-scale">
      <div
        v-for="rating in 5"
        :key="rating"
        @click="selectRating(rating)"
        :class="['likert-option', {
          'selected-rating': rating === modelValue,
          'size-1': rating === 1 || rating === 5,
          'size-2': rating === 2 || rating === 4,
          'size-3': rating === 3,
          'green-tone': rating === 1 || rating === 2,
          'purple-tone': rating === 4 || rating === 5,
          'gray-tone': rating === 3,
          'disabled-rating': disabled
        }]"
      >
        <span class="likert-circle">
          <template v-if="rating === modelValue">
            <v-icon class="white-icon">mdi-check</v-icon>
          </template>
        </span>
      </div>
    </div>
    <span class="likert-label-text">Schlecht</span>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, watch } from 'vue';

const props = defineProps({
  modelValue: { type: Number, default: null },
  disabled: { type: Boolean, default: false } // Neues Prop für das Disabled-Flag
});
const emit = defineEmits(['update:modelValue']);


function selectRating(rating) {
  if (props.disabled) return; // Keine Aktion, wenn disabled aktiv ist

  if (rating === props.modelValue) {
    emit('update:modelValue', null); // Zurücksetzen auf null
  } else {
    emit('update:modelValue', rating); // Den neuen Wert setzen
  }
}
</script>


<style scoped>
.likert-scale-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 10px;
}

.likert-scale {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin: 0 20px;
  gap: 5vh;
}

.likert-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: opacity 0.3s, cursor 0.3s;
}

.disabled-rating {
  cursor: not-allowed;
  opacity: 0.5; /* Inaktiver Stil */
}

.likert-circle {
  border: 2.5px solid #C8E6C9;
  border-radius: 50%;
  margin-bottom: 4px;
  transition: background-color 0.3s, border-color 0.3s, transform 0.3s;
  display: flex;
  justify-content: center;
  align-items: center;
}

.size-1 .likert-circle {
  width: 44px;
  height: 44px;
}

.size-2 .likert-circle {
  width: 36px;
  height: 36px;
}

.size-3 .likert-circle {
  width: 28px;
  height: 28px;
}

.green-tone .likert-circle {
  border-color: #66BB6A;
}

.purple-tone .likert-circle {
  border-color: #AB47BC;
}

.gray-tone .likert-circle {
  border-color: #BDBDBD;
}

.selected-rating.green-tone .likert-circle {
  background-color: #66BB6A;
}

.selected-rating.purple-tone .likert-circle {
  background-color: #AB47BC;
}

.selected-rating.gray-tone .likert-circle {
  background-color: #BDBDBD;
}

/* Updated hover styles */
.likert-option:hover .likert-circle {
  transform: scale(1.1);
}

.green-tone:hover .likert-circle {
  background-color: #68c66b;
  border-color: #54a356;
}

.purple-tone:hover .likert-circle {
  background-color: #bb55c1;
  border-color: #8e4a9a;
}

.gray-tone:hover .likert-circle {
  background-color: #d3d3d3;
  border-color: #515151;
}
</style>

