<template>
  <div class="binary-likert-scale-container">
    <span class="binary-label-text">Ja</span>
    <div class="binary-likert-scale">
      <div
        class="binary-option green-tone"
        :class="{
          'selected-yes': modelValue === 1,
          'disabled-option': disabled
        }"
        @click="selectOption(1)"
      >
        <span class="binary-circle">
          <template v-if="modelValue === 1">
            <v-icon class="white-icon">mdi-check</v-icon>
          </template>
        </span>
      </div>
      <div
        class="binary-option purple-tone"
        :class="{
          'selected-no': modelValue === 2,
          'disabled-option': disabled
        }"
        @click="selectOption(2)"
      >
        <span class="binary-circle">
          <template v-if="modelValue === 2">
            <v-icon class="white-icon">mdi-check</v-icon>
          </template>
        </span>
      </div>
    </div>
    <span class="binary-label-text">Nein</span>
  </div>
</template>


<script setup>
import { defineProps, defineEmits, watch } from 'vue';

// Props für modelValue und disabled
const props = defineProps({
  modelValue: { type: Number, default: null },
  disabled: { type: Boolean, default: false }
});

const emit = defineEmits(['update:modelValue']);


// Option auswählen, wenn nicht disabled
function selectOption(value) {
  if (props.disabled) return; // Keine Aktion, wenn disabled aktiv ist

  if (value === props.modelValue) {
    emit('update:modelValue', null); // Zurücksetzen auf null
  } else {
    emit('update:modelValue', value); // Den neuen Wert setzen
  }
}
</script>


<style scoped>
.binary-likert-scale-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 10px;
}

.binary-likert-scale {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin: 0 20px;
  gap: 10vh;
}

.binary-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: opacity 0.3s, cursor 0.3s;
}

.binary-circle {
  width: 44px;
  height: 44px;
  border: 2.5px solid #BDBDBD;
  border-radius: 50%;
  margin-bottom: 4px;
  transition: background-color 0.3s, border-color 0.3s, transform 0.3s;
  display: flex;
  justify-content: center;
  align-items: center;
}

.green-tone .binary-circle {
  border-color: #66BB6A;
}

.purple-tone .binary-circle {
  border-color: #AB47BC;
}

.selected-yes .binary-circle {
  background-color: #66BB6A;
  border-color: #66BB6A;
}

.selected-no .binary-circle {
  background-color: #AB47BC;
  border-color: #AB47BC;
}

/* Hover-Effekt */
.binary-option:hover .binary-circle {
  transform: scale(1.1);
}

.green-tone:hover .binary-circle {
  background-color: #68c66b;
  border-color: #54a356;
}

.purple-tone:hover .binary-circle {
  background-color: #bb55c1;
  border-color: #8e4a9a;
}

/* Disabled-Stile */
.disabled-option {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>
