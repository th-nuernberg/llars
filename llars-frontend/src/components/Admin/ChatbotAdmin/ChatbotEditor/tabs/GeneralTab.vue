<!--
  ChatbotEditor - General Tab

  Basic chatbot settings including name, description, icon, color, and status.
-->
<template>
  <v-form ref="formGeneral">
    <v-row>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="formData.name"
          label="Technischer Name"
          hint="Eindeutiger Bezeichner (z.B. support-bot)"
          persistent-hint
          :rules="[rules.required]"
          variant="outlined"
          density="comfortable"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="formData.display_name"
          label="Anzeigename"
          hint="Name wie er Benutzern angezeigt wird"
          persistent-hint
          :rules="[rules.required]"
          variant="outlined"
          density="comfortable"
        />
      </v-col>
      <v-col cols="12">
        <v-textarea
          v-model="formData.description"
          label="Beschreibung"
          hint="Kurze Beschreibung des Chatbot-Zwecks"
          persistent-hint
          rows="2"
          variant="outlined"
          density="comfortable"
        />
      </v-col>

      <!-- Icon Selection -->
      <v-col cols="12" md="6">
        <v-select
          v-model="formData.icon"
          label="Icon"
          :items="iconOptions"
          variant="outlined"
          density="comfortable"
        >
          <template #selection="{ item }">
            <LIcon class="mr-2">{{ item.value }}</LIcon>
            {{ item.title }}
          </template>
          <template #item="{ props, item }">
            <v-list-item v-bind="props">
              <template #prepend>
                <LIcon>{{ item.value }}</LIcon>
              </template>
            </v-list-item>
          </template>
          <template #append>
            <v-btn
              icon
              variant="text"
              size="small"
              :loading="generatingIcon"
              :disabled="generatingIcon"
              @click.stop="$emit('generate-icon')"
            >
              <LIcon>mdi-auto-fix</LIcon>
              <v-tooltip activator="parent" location="top">
                {{ isEdit ? 'Icon vorschlagen (LLM)' : 'Zufälliges Icon' }}
              </v-tooltip>
            </v-btn>
          </template>
        </v-select>
      </v-col>

      <!-- Color Picker -->
      <v-col cols="12" md="6">
        <v-text-field
          v-model="formData.color"
          label="Farbe"
          variant="outlined"
          density="comfortable"
        >
          <template #prepend-inner>
            <input
              v-model="formData.color"
              type="color"
              style="width: 32px; height: 32px; border: none; cursor: pointer"
            >
          </template>
          <template #append>
            <v-btn
              icon
              variant="text"
              size="small"
              :loading="generatingColor"
              :disabled="generatingColor"
              @click.stop="$emit('generate-color')"
            >
              <LIcon>mdi-auto-fix</LIcon>
              <v-tooltip activator="parent" location="top">
                {{ isEdit ? 'Farbe vorschlagen (LLM/Brand)' : 'Zufällige Farbe' }}
              </v-tooltip>
            </v-btn>
          </template>
        </v-text-field>
      </v-col>

      <!-- Fallback Message -->
      <v-col cols="12">
        <v-textarea
          v-model="formData.fallback_message"
          label="Fallback-Nachricht"
          hint="Nachricht bei Fehlern oder wenn keine Antwort möglich"
          persistent-hint
          rows="2"
          variant="outlined"
          density="comfortable"
        />
      </v-col>

      <!-- Status Switches -->
      <v-col cols="12" md="6">
        <v-switch
          v-model="formData.is_active"
          label="Chatbot aktiv"
          color="success"
          hide-details
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch
          v-model="formData.is_public"
          label="Öffentlich verfügbar"
          color="primary"
          hide-details
        />
      </v-col>
    </v-row>
  </v-form>
</template>

<script setup>
/**
 * @component GeneralTab
 * @description General settings tab for chatbot configuration.
 */

defineProps({
  /** Form data object (v-model binding from parent) */
  formData: {
    type: Object,
    required: true
  },
  /** Available icon options */
  iconOptions: {
    type: Array,
    required: true
  },
  /** Validation rules */
  rules: {
    type: Object,
    required: true
  },
  /** Whether editing existing chatbot */
  isEdit: {
    type: Boolean,
    default: false
  },
  /** Icon generation loading state */
  generatingIcon: {
    type: Boolean,
    default: false
  },
  /** Color generation loading state */
  generatingColor: {
    type: Boolean,
    default: false
  }
});

defineEmits(['generate-icon', 'generate-color']);
</script>
