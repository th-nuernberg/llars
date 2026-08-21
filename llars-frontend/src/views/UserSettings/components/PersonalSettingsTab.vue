<template>
  <div class="personal-settings" role="region" aria-label="Persönliche Einstellungen">
    <!-- Redeem Invitation Code Section -->
    <!-- Always visible to ANY logged-in user (not gated behind canCreateReferrals):
         an existing participant pastes a study code/slug to join + be attributed. -->
    <section class="settings-panel" role="group" aria-labelledby="redeem-title">
      <header class="panel-header">
        <LIcon size="18" class="panel-icon">mdi-ticket-confirmation</LIcon>
        <h2 id="redeem-title" class="panel-title">{{ $t('userSettings.personal.redeem.title') }}</h2>
      </header>

      <div class="panel-content">
        <p class="section-description" id="redeem-description">
          {{ $t('userSettings.personal.redeem.description') }}
        </p>

        <form class="redeem-row" @submit.prevent="handleRedeem">
          <input
            v-model="redeemCode"
            type="text"
            class="redeem-input"
            :placeholder="$t('auth.inviteCode')"
            :aria-label="$t('auth.inviteCode')"
            :disabled="redeemLoading"
            autocomplete="off"
          />
          <LBtn
            type="submit"
            variant="primary"
            :loading="redeemLoading"
            :disabled="!redeemCode.trim() || redeemLoading"
          >
            {{ $t('userSettings.personal.redeem.submit') }}
          </LBtn>
        </form>

        <!-- Inline error (mirrors backend message) -->
        <div v-if="redeemError" class="redeem-error" role="alert">
          <LIcon size="16">mdi-alert-circle</LIcon>
          <span>{{ redeemError }}</span>
        </div>

        <!-- Inline success + jump-to-study action -->
        <div v-if="redeemSuccess" class="redeem-success" role="status">
          <LIcon size="16">mdi-check-circle</LIcon>
          <span>{{ redeemSuccessMessage }}</span>
          <LBtn
            v-if="redeemScenarioId"
            variant="accent"
            size="small"
            @click="goToStudy"
          >
            {{ $t('userSettings.personal.redeem.goToStudy') }}
          </LBtn>
        </div>
      </div>
    </section>

    <!-- Profile / Demographics Section -->
    <!-- Lets every user review the email we have on file (read-only — it lives
         in Authentik, not editable here) and view/change the demographic data
         they gave in the first-login survey. Saves via POST /api/user/demographics
         (the same endpoint the survey uses; idempotent, keeps completed_at). -->
    <section class="settings-panel" role="group" aria-labelledby="profile-title">
      <header class="panel-header">
        <LIcon size="18" class="panel-icon">mdi-account-details</LIcon>
        <h2 id="profile-title" class="panel-title">{{ $t('userSettings.personal.profile.title') }}</h2>
      </header>

      <div class="panel-content">
        <p class="section-description">{{ $t('userSettings.personal.profile.description') }}</p>

        <!-- Stored email (read-only) -->
        <div class="profile-email-row">
          <LIcon size="16">mdi-email-outline</LIcon>
          <span class="profile-email-label">{{ $t('userSettings.personal.profile.emailLabel') }}</span>
          <code v-if="profileEmail" class="profile-email-value">{{ profileEmail }}</code>
          <span v-else class="profile-email-empty">{{ $t('userSettings.personal.profile.emailNone') }}</span>
        </div>

        <!-- Email-contact consent: grant/revoke storing the email for future
             studies ("jederzeit widerrufbar"). Only shown when the user has a
             referral registration that can carry the flag. -->
        <div v-if="emailConsent !== null" class="email-consent-row">
          <LCheckbox
            :model-value="emailConsent"
            :disabled="emailConsentSaving"
            :label="$t('userSettings.personal.profile.emailConsentLabel')"
            data-testid="email-consent-toggle"
            @update:model-value="setEmailConsent"
          />
        </div>

        <!-- Demographics (editable) -->
        <div
          v-for="grp in demoGroups"
          :key="grp.key"
          class="demo-group"
          role="radiogroup"
          :aria-label="$t(`onboarding.demographics.${grp.key}.label`)"
        >
          <span class="demo-group-label">{{ $t(`onboarding.demographics.${grp.key}.label`) }}</span>
          <div class="demo-options">
            <button
              v-for="opt in grp.options"
              :key="opt"
              type="button"
              role="radio"
              class="demo-chip"
              :class="{ selected: demo[grp.field] === opt }"
              :aria-checked="demo[grp.field] === opt"
              @click="demo[grp.field] = opt"
            >
              {{ demoLabel(grp.key, opt) }}
            </button>
          </div>
        </div>

        <div class="demo-group">
          <label class="demo-group-label" for="demo-profession">
            {{ $t('onboarding.demographics.profession.label') }}
          </label>
          <input
            id="demo-profession"
            v-model="demo.profession"
            type="text"
            class="redeem-input"
            maxlength="255"
            :placeholder="$t('onboarding.demographics.profession.placeholder')"
          />
        </div>

        <div class="demo-actions">
          <LBtn variant="primary" :loading="demoSaving" :disabled="demoSaving" @click="saveDemographics">
            {{ $t('userSettings.personal.profile.save') }}
          </LBtn>
          <span v-if="demoSaved" class="demo-saved" role="status">
            <LIcon size="16">mdi-check-circle</LIcon>
            {{ $t('userSettings.personal.profile.saved') }}
          </span>
        </div>
      </div>
    </section>

    <!-- Avatar Section -->
    <section class="settings-panel" role="group" aria-labelledby="avatar-title">
      <header class="panel-header">
        <LIcon size="18" class="panel-icon">mdi-account-circle</LIcon>
        <h2 id="avatar-title" class="panel-title">{{ $t('userSettings.personal.avatar.title') }}</h2>
      </header>

      <div class="panel-content">
        <div class="avatar-row">
          <div class="avatar-preview">
            <LAvatar
              :src="avatarUrl"
              :seed="globalAvatarSeed"
              :username="username"
              size="xl"
              class="settings-avatar"
              :aria-label="$t('userSettings.personal.avatar.current')"
            />
          </div>

          <div class="avatar-actions">
            <p class="action-hint">{{ $t('userSettings.personal.avatar.hint') }}</p>
            <div class="action-buttons" role="group" aria-label="Avatar-Aktionen">
              <button
                class="action-btn primary"
                @click="triggerFileInput"
                :aria-label="$t('userSettings.personal.avatar.upload')"
              >
                <LIcon size="16">mdi-upload</LIcon>
                <span>{{ $t('userSettings.personal.avatar.upload') }}</span>
              </button>
              <input
                ref="fileInput"
                type="file"
                accept="image/png,image/jpeg,image/gif,image/webp"
                class="sr-only"
                @change="handleFileSelect"
                :aria-label="$t('userSettings.personal.avatar.selectFile')"
              />

              <button
                class="action-btn"
                @click="regenerateAvatar"
                :aria-label="$t('userSettings.personal.avatar.regenerate')"
              >
                <LIcon size="16">mdi-refresh</LIcon>
                <span>{{ $t('userSettings.personal.avatar.regenerate') }}</span>
              </button>

              <button
                v-if="avatarUrl"
                class="action-btn danger"
                @click="deleteAvatar"
                :aria-label="$t('userSettings.personal.avatar.delete')"
              >
                <LIcon size="16">mdi-delete</LIcon>
                <span>{{ $t('userSettings.personal.avatar.delete') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Collab Color Section -->
    <section class="settings-panel" role="group" aria-labelledby="color-title">
      <header class="panel-header">
        <LIcon size="18" class="panel-icon">mdi-palette</LIcon>
        <h2 id="color-title" class="panel-title">{{ $t('userSettings.personal.collabColor.title') }}</h2>
      </header>

      <div class="panel-content">
        <p class="section-description" id="color-description">
          {{ $t('userSettings.personal.collabColor.description') }}
        </p>

        <div
          class="color-grid"
          role="radiogroup"
          aria-labelledby="color-description"
          @keydown="handleColorKeydown"
        >
          <button
            v-for="(color, index) in predefinedColors"
            :key="color"
            type="button"
            role="radio"
            class="color-swatch"
            :class="{ selected: collabColor === color }"
            :style="{ '--swatch-color': color }"
            :aria-checked="collabColor === color"
            :aria-label="`Farbe ${index + 1}`"
            :tabindex="collabColor === color ? 0 : -1"
            @click="selectColor(color)"
          >
            <LIcon v-if="collabColor === color" size="16" color="white" class="check-mark">mdi-check</LIcon>
          </button>

          <div class="custom-color-box">
            <input
              type="color"
              v-model="customColor"
              class="custom-color-input"
              @change="selectColor(customColor)"
              :aria-label="$t('userSettings.personal.collabColor.custom')"
            />
            <span class="custom-label">{{ $t('userSettings.personal.collabColor.custom') }}</span>
          </div>
        </div>

        <div v-if="collabColor" class="color-preview-bar" aria-live="polite">
          <span class="preview-label">{{ $t('userSettings.personal.collabColor.preview') }}</span>
          <div class="preview-sample" :style="{ backgroundColor: collabColor }">
            <span class="preview-cursor" :style="{ borderColor: collabColor }"></span>
          </div>
          <code class="preview-code">{{ collabColor }}</code>
        </div>
      </div>
    </section>

    <!-- Theme Section -->
    <section class="settings-panel" role="group" aria-labelledby="theme-title">
      <header class="panel-header">
        <LIcon size="18" class="panel-icon">llars:system-theme</LIcon>
        <h2 id="theme-title" class="panel-title">{{ $t('userSettings.personal.preferences.theme') }}</h2>
      </header>

      <div class="panel-content">
        <p class="section-description" id="theme-description">
          {{ $t('userSettings.personal.preferences.themeHint') }}
        </p>

        <div class="theme-cards" role="radiogroup" aria-labelledby="theme-description">
          <button
            v-for="option in themeOptions"
            :key="option.value"
            type="button"
            role="radio"
            class="theme-card"
            :class="{ selected: themePreference === option.value }"
            :aria-checked="themePreference === option.value"
            :aria-label="$t('theme.' + option.value)"
            @click="setTheme(option.value)"
          >
            <div class="theme-icon-wrapper" :class="option.value">
              <LIcon size="24">{{ option.icon }}</LIcon>
            </div>
            <span class="theme-name">{{ $t('theme.' + option.value) }}</span>
            <LIcon v-if="themePreference === option.value" size="16" class="theme-check">mdi-check-circle</LIcon>
          </button>
        </div>
      </div>
    </section>

    <!-- Language Section -->
    <section class="settings-panel" role="group" aria-labelledby="language-title">
      <header class="panel-header">
        <LIcon size="18" class="panel-icon">mdi-translate</LIcon>
        <h2 id="language-title" class="panel-title">{{ $t('userSettings.personal.preferences.language') }}</h2>
      </header>

      <div class="panel-content">
        <p class="section-description" id="language-description">
          {{ $t('userSettings.personal.preferences.languageHint') }}
        </p>

        <div class="language-options" role="radiogroup" aria-labelledby="language-description">
          <button
            v-for="lang in languages"
            :key="lang.value"
            type="button"
            role="radio"
            class="language-option"
            :class="{ selected: selectedLanguage === lang.value }"
            :aria-checked="selectedLanguage === lang.value"
            @click="handleLanguageChange(lang.value)"
          >
            <span class="lang-flag">{{ lang.flag }}</span>
            <span class="lang-label">{{ lang.label }}</span>
            <LIcon v-if="selectedLanguage === lang.value" size="16" class="lang-check">mdi-check</LIcon>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, defineEmits } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import LIcon from '@/components/common/LIcon.vue'
import LAvatar from '@/components/common/LAvatar.vue'
import LBtn from '@/components/common/LBtn.vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { useAppTheme } from '@/composables/useAppTheme'
import { useReferralRedeem } from '@/composables/useReferralRedeem'
import { useSnackbar } from '@/composables/useSnackbar'
import { COLLAB_COLOR_PRESETS } from '@/constants/colors'

const emit = defineEmits(['save-status'])

const { t, locale } = useI18n()
const router = useRouter()
const { showSuccess, showError } = useSnackbar()

// --- Redeem invitation code (join a study as an existing user) ---
const { loading: redeemLoading, redeem } = useReferralRedeem()
const redeemCode = ref('')
const redeemError = ref('')
const redeemSuccess = ref(false)
const redeemSuccessMessage = ref('')
const redeemScenarioId = ref(null)

async function handleRedeem() {
  redeemError.value = ''
  redeemSuccess.value = false
  const code = redeemCode.value.trim()
  if (!code) return

  const { success, data, error } = await redeem(code)
  if (success) {
    redeemScenarioId.value = data.target_scenario_id || null
    // already_enrolled → "you were already in this study"; otherwise → joined.
    redeemSuccessMessage.value = data.already_enrolled
      ? t('userSettings.personal.redeem.alreadyEnrolled')
      : t('userSettings.personal.redeem.success')
    redeemSuccess.value = true
    showSuccess(redeemSuccessMessage.value)
    redeemCode.value = ''
  } else {
    // Backend messages are localized German; fall back to a generic i18n string
    // for the empty/transport sentinels emitted by the composable.
    redeemError.value = (error === 'empty' || error === 'request_failed')
      ? t('userSettings.personal.redeem.error')
      : error
    showError(redeemError.value)
  }
}

function goToStudy() {
  if (redeemScenarioId.value) {
    router.push(`/scenarios/${redeemScenarioId.value}/evaluate`)
  }
}

// --- Profile: stored email (read-only) + demographics (view/edit) ---
// Reuses the survey's controlled vocabularies + i18n labels
// (onboarding.demographics.*). "no_answer" shares a single label outside the
// per-group block, hence the special case in demoLabel().
const profileEmail = ref(null)
const emailConsent = ref(null)          // null = not applicable (no referral reg)
const emailConsentSaving = ref(false)
const demoReferralLinkId = ref(null)
const demoSaving = ref(false)
const demoSaved = ref(false)
const demo = ref({ gender: null, age_range: null, education: null, profession: '' })

const demoGroups = [
  { key: 'gender', field: 'gender', options: ['female', 'male', 'non_binary', 'no_answer'] },
  { key: 'age', field: 'age_range', options: ['under_29', '30_49', '50_64', '65_plus', 'no_answer'] },
  { key: 'education', field: 'education', options: ['phd', 'master', 'bachelor', 'vocational', 'abitur', 'realschule', 'no_formal', 'no_answer'] },
]

function demoLabel(group, key) {
  return key === 'no_answer'
    ? t('onboarding.demographics.no_answer')
    : t(`onboarding.demographics.${group}.${key}`)
}

async function loadDemographics() {
  try {
    const { data } = await axios.get('/api/user/demographics')
    profileEmail.value = data.email || null
    emailConsent.value = data.email_contact_consent  // true | false | null
    demoReferralLinkId.value = data.referral_link_id || null
    if (data.demographics) {
      demo.value = {
        gender: data.demographics.gender || null,
        age_range: data.demographics.age_range || null,
        education: data.demographics.education || null,
        profession: data.demographics.profession || '',
      }
    }
  } catch (error) {
    console.error('Failed to load demographics:', error)
  }
}

// Grant/revoke the "store my email for future studies" consent ("jederzeit
// widerrufbar"). Persists to the referral registration's metadata via the
// dedicated endpoint.
async function setEmailConsent(value) {
  emailConsentSaving.value = true
  try {
    const { data } = await axios.post('/api/user/demographics/email-consent', { consent: value })
    emailConsent.value = data.email_contact_consent
    showSuccess(t('userSettings.personal.profile.emailConsentSaved'))
  } catch (error) {
    emailConsent.value = !value  // revert optimistic toggle
    showError(t('userSettings.personal.profile.saveError'))
  } finally {
    emailConsentSaving.value = false
  }
}

async function saveDemographics() {
  demoSaving.value = true
  demoSaved.value = false
  try {
    const payload = {
      gender: demo.value.gender,
      age_range: demo.value.age_range,
      education: demo.value.education,
      profession: (demo.value.profession || '').trim() || null,
    }
    if (demoReferralLinkId.value) payload.referral_link_id = demoReferralLinkId.value
    await axios.post('/api/user/demographics', payload)
    demoSaved.value = true
    showSuccess(t('userSettings.personal.profile.saved'))
  } catch (error) {
    showError(t('userSettings.personal.profile.saveError'))
  } finally {
    demoSaving.value = false
  }
}

// Auth composable for avatar management
const {
  tokenParsed,
  avatarSeed: globalAvatarSeed,
  avatarUrl: globalAvatarUrl,
  collabColor: globalCollabColor,
  uploadAvatar: authUploadAvatar,
  regenerateAvatar: authRegenerateAvatar,
  resetAvatar: authResetAvatar,
  updateCollabColor
} = useAuth()

// Theme composable
const {
  themePreference,
  themeOptions,
  setThemePreference
} = useAppTheme()

const fileInput = ref(null)
const customColor = ref('#b0ca97')
const selectedLanguage = ref('de')
const collabColor = ref(null)

// Use global LLARS color presets
const predefinedColors = COLLAB_COLOR_PRESETS

const languages = [
  { value: 'de', label: 'Deutsch', flag: '🇩🇪' },
  { value: 'en', label: 'English', flag: '🇬🇧' }
]

// Computed
const username = computed(() => tokenParsed.value?.preferred_username || '')
const avatarUrl = computed(() => globalAvatarUrl.value)

// Auto-save with debounce
const debouncedSaveSettings = useDebounceFn(async () => {
  try {
    emit('save-status', 'saving')

    // Update collab color via useAuth (handles backend + global state + broadcasts event)
    // This must happen FIRST so the watch in the collab editor panes triggers properly
    if (collabColor.value !== globalCollabColor.value) {
      await updateCollabColor(collabColor.value)
    }

    // Save other preferences (NOT collab_color - already saved by updateCollabColor)
    await axios.put('/api/user/settings', {
      preferences: {
        theme: themePreference.value,
        language: selectedLanguage.value
      }
    })

    emit('save-status', 'saved')
  } catch (error) {
    console.error('Failed to save settings:', error)
    emit('save-status', null)
  }
}, 500)

// Load settings on mount
onMounted(async () => {
  await Promise.all([
    loadSettings(),
    loadDemographics()
  ])
})

// Watch for external collab color changes (e.g., from AppBar)
watch(globalCollabColor, (newColor) => {
  if (newColor && newColor !== collabColor.value) {
    collabColor.value = newColor
  }
})

async function loadSettings() {
  try {
    const response = await axios.get('/api/user/settings')
    const data = response.data.settings

    collabColor.value = data.collab_color || globalCollabColor.value

    if (data.preferences) {
      selectedLanguage.value = data.preferences.language || locale.value
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
  }
}

// Color selection with auto-save
function selectColor(color) {
  collabColor.value = color
  debouncedSaveSettings()
}

// Theme selection with auto-save
function setTheme(value) {
  setThemePreference(value)
  debouncedSaveSettings()
}

// Language change with auto-save
function handleLanguageChange(newLang) {
  selectedLanguage.value = newLang
  if (newLang !== locale.value) {
    locale.value = newLang
  }
  debouncedSaveSettings()
}

// Color keyboard navigation
function handleColorKeydown(event) {
  const colors = predefinedColors
  const currentIndex = colors.indexOf(collabColor.value)
  let newIndex = currentIndex

  if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
    newIndex = (currentIndex + 1) % colors.length
    event.preventDefault()
  } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
    newIndex = currentIndex <= 0 ? colors.length - 1 : currentIndex - 1
    event.preventDefault()
  }

  if (newIndex !== currentIndex) {
    selectColor(colors[newIndex])
  }
}

// Avatar functions
function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return

  try {
    emit('save-status', 'saving')
    const result = await authUploadAvatar(file)
    if (result.success) {
      emit('save-status', 'saved')
    } else {
      console.error('Failed to upload avatar:', result.error)
      emit('save-status', null)
    }
  } catch (error) {
    console.error('Failed to upload avatar:', error)
    emit('save-status', null)
  } finally {
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function deleteAvatar() {
  try {
    emit('save-status', 'saving')
    const result = await authResetAvatar()
    if (result.success) {
      emit('save-status', 'saved')
    } else {
      emit('save-status', null)
    }
  } catch (error) {
    console.error('Failed to delete avatar:', error)
    emit('save-status', null)
  }
}

async function regenerateAvatar() {
  try {
    emit('save-status', 'saving')
    const result = await authRegenerateAvatar()
    if (result.success) {
      emit('save-status', 'saved')
    } else {
      emit('save-status', null)
    }
  } catch (error) {
    console.error('Failed to regenerate avatar:', error)
    emit('save-status', null)
  }
}
</script>

<style scoped>
/* ============================================
   LLARS Settings Panels - SOTA Design
   ============================================ */

.personal-settings {
  --llars-primary: #b0ca97;
  --llars-accent: #88c4c8;
  --llars-radius: 16px 4px 16px 4px;
  --llars-radius-sm: 8px 2px 8px 2px;

  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Screen reader only */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* ============================================
   Panel Design (like the collab workspaces)
   ============================================ */

.settings-panel {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.panel-icon {
  color: var(--llars-primary);
  opacity: 0.9;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  color: rgb(var(--v-theme-on-surface));
}

.panel-content {
  padding: 16px;
}

.section-description {
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0 0 16px 0;
  line-height: 1.5;
}

/* ============================================
   Redeem Invitation Code
   ============================================ */

.redeem-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.redeem-input {
  flex: 1;
  min-width: 200px;
  padding: 10px 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: var(--llars-radius-sm);
  background: rgba(var(--v-theme-on-surface), 0.02);
  color: rgb(var(--v-theme-on-surface));
  font-size: 14px;
  transition: border-color 0.15s ease;
}

.redeem-input:focus {
  outline: none;
  border-color: var(--llars-primary);
}

.redeem-error {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 14px;
  background: rgba(232, 160, 135, 0.1);
  border: 1px solid rgba(232, 160, 135, 0.3);
  border-radius: var(--llars-radius-sm);
  color: #e8a087;
  font-size: 13px;
  font-weight: 500;
}

.redeem-success {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 12px;
  padding: 10px 14px;
  background: rgba(152, 212, 187, 0.12);
  border: 1px solid rgba(152, 212, 187, 0.35);
  border-radius: var(--llars-radius-sm);
  color: rgb(var(--v-theme-on-surface));
  font-size: 13px;
  font-weight: 500;
}

.redeem-success .l-icon,
.redeem-success > span:first-of-type {
  color: #5bb89a;
}

/* ============================================
   Profile / Demographics Section
   ============================================ */

.profile-email-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding: 10px 14px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: var(--llars-radius-sm);
}

.email-consent-row {
  margin: -8px 0 18px;
}
.email-consent-row :deep(.l-checkbox__label),
.email-consent-row :deep(label) {
  line-height: 1.45;
  font-size: 13px;
}

.profile-email-label {
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.profile-email-value {
  font-size: 13px;
  padding: 2px 8px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 4px;
  color: rgb(var(--v-theme-on-surface));
  word-break: break-all;
}

.profile-email-empty {
  font-size: 13px;
  font-style: italic;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.demo-group {
  margin-bottom: 18px;
}

.demo-group-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 8px;
}

.demo-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.demo-chip {
  padding: 8px 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: var(--llars-radius-sm);
  background: rgba(var(--v-theme-on-surface), 0.02);
  color: rgba(var(--v-theme-on-surface), 0.8);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.demo-chip:hover {
  background: rgba(var(--v-theme-on-surface), 0.06);
  border-color: rgba(var(--v-theme-on-surface), 0.2);
}

.demo-chip:focus {
  outline: 2px solid var(--llars-primary);
  outline-offset: 2px;
}

.demo-chip.selected {
  border-color: var(--llars-primary);
  background: rgba(176, 202, 151, 0.12);
  color: var(--llars-primary);
  font-weight: 600;
}

.demo-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
}

.demo-saved {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #5bb89a;
}

/* ============================================
   Avatar Section
   ============================================ */

.avatar-row {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.avatar-preview {
  flex-shrink: 0;
}

.settings-avatar {
  width: 100px !important;
  height: 100px !important;
  border-radius: 20px 6px 20px 6px !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.settings-avatar :deep(.l-avatar__fallback) {
  font-size: 2rem !important;
}

.avatar-actions {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-hint {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: var(--llars-radius-sm);
  background: rgba(var(--v-theme-on-surface), 0.02);
  color: rgba(var(--v-theme-on-surface), 0.8);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: rgba(var(--v-theme-on-surface), 0.06);
  border-color: rgba(var(--v-theme-on-surface), 0.2);
}

.action-btn:focus {
  outline: 2px solid var(--llars-primary);
  outline-offset: 2px;
}

.action-btn.primary {
  background: var(--llars-primary);
  border-color: var(--llars-primary);
  color: white;
}

.action-btn.primary:hover {
  filter: brightness(1.05);
}

.action-btn.danger {
  color: #e8a087;
  border-color: rgba(232, 160, 135, 0.3);
}

.action-btn.danger:hover {
  background: rgba(232, 160, 135, 0.1);
  border-color: #e8a087;
}

/* ============================================
   Color Picker
   ============================================ */

.color-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.color-swatch {
  width: 40px;
  height: 40px;
  border-radius: var(--llars-radius-sm);
  border: 2px solid transparent;
  background: var(--swatch-color);
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.color-swatch:hover {
  transform: scale(1.08);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.color-swatch:focus {
  outline: 2px solid var(--llars-primary);
  outline-offset: 3px;
}

.color-swatch.selected {
  border-color: rgb(var(--v-theme-on-surface));
  box-shadow: 0 0 0 3px rgb(var(--v-theme-surface)), 0 0 0 5px var(--llars-primary);
}

.check-mark {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

.custom-color-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.custom-color-input {
  width: 40px;
  height: 40px;
  padding: 0;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: var(--llars-radius-sm);
  cursor: pointer;
  transition: border-color 0.15s ease;
}

.custom-color-input:hover {
  border-color: var(--llars-primary);
}

.custom-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.color-preview-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding: 10px 14px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: var(--llars-radius-sm);
}

.preview-label {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.preview-sample {
  width: 60px;
  height: 24px;
  border-radius: 4px;
  position: relative;
}

.preview-cursor {
  position: absolute;
  left: 50%;
  top: -4px;
  width: 2px;
  height: 32px;
  background: currentColor;
  border: 2px solid;
  border-radius: 2px;
}

.preview-code {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 4px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* ============================================
   Theme Cards
   ============================================ */

.theme-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.theme-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 16px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.theme-card:hover {
  border-color: rgba(var(--v-theme-on-surface), 0.15);
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.theme-card:focus {
  outline: 2px solid var(--llars-primary);
  outline-offset: 2px;
}

.theme-card.selected {
  border-color: var(--llars-primary);
  background: rgba(176, 202, 151, 0.08);
}

.theme-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.theme-icon-wrapper.system {
  background: linear-gradient(135deg, #f5f5f5 50%, #333 50%);
  color: #666;
}

.theme-icon-wrapper.light {
  background: linear-gradient(135deg, #fff9c4 0%, #ffee58 100%);
  color: #f57f17;
}

.theme-icon-wrapper.dark {
  background: linear-gradient(135deg, #1a237e 0%, #311b92 100%);
  color: #b39ddb;
}

.theme-name {
  font-size: 13px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.theme-card.selected .theme-name {
  color: var(--llars-primary);
}

.theme-check {
  position: absolute;
  top: 8px;
  right: 8px;
  color: var(--llars-primary);
}

/* ============================================
   Language Options
   ============================================ */

.language-options {
  display: flex;
  gap: 12px;
}

.language-option {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: var(--llars-radius-sm);
  background: rgba(var(--v-theme-on-surface), 0.02);
  cursor: pointer;
  transition: all 0.15s ease;
}

.language-option:hover {
  border-color: rgba(var(--v-theme-on-surface), 0.15);
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.language-option:focus {
  outline: 2px solid var(--llars-primary);
  outline-offset: 2px;
}

.language-option.selected {
  border-color: var(--llars-primary);
  background: rgba(176, 202, 151, 0.08);
}

.lang-flag {
  font-size: 24px;
}

.lang-label {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.language-option.selected .lang-label {
  color: var(--llars-primary);
}

.lang-check {
  color: var(--llars-primary);
}

/* ============================================
   Mobile Responsive
   ============================================ */

@media (max-width: 600px) {
  .avatar-row {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .action-hint {
    text-align: center;
  }

  .action-buttons {
    justify-content: center;
  }

  .theme-cards {
    grid-template-columns: 1fr;
  }

  .language-options {
    flex-direction: column;
  }
}
</style>
