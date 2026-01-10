<template>
  <div class="register-page" :class="{ 'dark-mode': isDarkMode, 'is-mobile': isMobile, 'is-ios': isIOS }">
    <div class="paint-strokes">
      <div v-for="n in 10" :key="n"></div>
    </div>

    <div class="register-container">
      <div class="register-card">
        <!-- Header with Logo -->
        <div class="register-header">
          <img src="@/assets/logo/llars-logo.png" alt="LLARS Logo" class="register-logo" />
          <h1 class="register-title">Registrierung</h1>
          <p v-if="campaignName" class="register-subtitle">{{ campaignName }}</p>
          <p v-else class="register-subtitle">Erstelle deinen Account</p>
        </div>

        <!-- Registration Form -->
        <div class="register-form" data-testid="register-form">
          <v-form @submit.prevent="handleRegister">
            <!-- Referral Code -->
            <v-text-field
              v-model="referralCode"
              label="Einladungscode"
              data-testid="referral-code-input"
              autocomplete="off"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-ticket-confirmation"
              :disabled="isRegistering || codeFromUrl"
              :readonly="codeFromUrl"
              :error-messages="codeError"
              :loading="isValidating"
              @blur="validateCode"
              class="register-field"
              hide-details="auto"
            >
              <template #append-inner>
                <v-icon v-if="codeValid" color="success" size="small">mdi-check-circle</v-icon>
              </template>
            </v-text-field>

            <!-- Username -->
            <v-text-field
              v-model="username"
              label="Benutzername"
              data-testid="username-input"
              autocomplete="username"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-account"
              :disabled="isRegistering"
              :rules="usernameRules"
              class="register-field"
              hide-details="auto"
            />

            <!-- Email -->
            <v-text-field
              v-model="email"
              label="E-Mail"
              type="email"
              data-testid="email-input"
              autocomplete="email"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-email"
              :disabled="isRegistering"
              :rules="emailRules"
              class="register-field"
              hide-details="auto"
            />

            <!-- Password -->
            <v-text-field
              v-model="password"
              label="Passwort"
              data-testid="password-input"
              autocomplete="new-password"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-lock"
              :type="showPassword ? 'text' : 'password'"
              :disabled="isRegistering"
              :rules="passwordRules"
              hint="Mindestens 8 Zeichen"
              class="register-field"
              hide-details="auto"
            >
              <template #append-inner>
                <v-icon
                  :icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                  @click="showPassword = !showPassword"
                  class="cursor-pointer"
                />
              </template>
            </v-text-field>

            <!-- Confirm Password -->
            <v-text-field
              v-model="passwordConfirm"
              label="Passwort bestätigen"
              data-testid="password-confirm-input"
              autocomplete="new-password"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-lock-check"
              :type="showPassword ? 'text' : 'password'"
              :disabled="isRegistering"
              :rules="passwordConfirmRules"
              @keyup.enter="handleRegister"
              class="register-field"
              hide-details="auto"
            />

            <!-- Display Name (Optional) -->
            <v-text-field
              v-model="displayName"
              label="Anzeigename (optional)"
              data-testid="display-name-input"
              autocomplete="name"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-card-account-details"
              :disabled="isRegistering"
              class="register-field"
              hide-details="auto"
            />

            <LBtn
              variant="primary"
              block
              size="large"
              @click="handleRegister"
              :loading="isRegistering"
              :disabled="!isFormValid"
              prepend-icon="mdi-account-plus"
              class="register-button"
              data-testid="register-btn"
            >
              Registrieren
            </LBtn>
          </v-form>

          <!-- Success Message -->
          <v-alert
            v-if="successMessage"
            type="success"
            variant="tonal"
            density="compact"
            class="register-message"
          >
            {{ successMessage }}
          </v-alert>

          <!-- Error Message -->
          <v-alert
            v-if="errorMessage"
            type="error"
            variant="tonal"
            density="compact"
            class="register-message"
            closable
            @click:close="errorMessage = ''"
          >
            {{ errorMessage }}
          </v-alert>
        </div>

        <!-- Footer with Login Link -->
        <div class="register-footer">
          <router-link to="/login" class="login-link">
            <v-icon size="small" class="mr-1">mdi-arrow-left</v-icon>
            Bereits registriert? Anmelden
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useMobile } from '@/composables/useMobile'
import { useReferralSystem } from '@/composables/useReferralSystem'

const props = defineProps({
  code: {
    type: String,
    default: ''
  }
})

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)
const { isMobile, isIOS } = useMobile()

const router = useRouter()
const route = useRoute()
const referral = useReferralSystem()

// Form fields
const referralCode = ref('')
const username = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const displayName = ref('')
const showPassword = ref(false)

// State
const isValidating = ref(false)
const isRegistering = ref(false)
const codeValid = ref(false)
const codeError = ref('')
const campaignName = ref('')
const assignedRole = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const codeFromUrl = ref(false)

// Validation rules
const usernameRules = [
  v => !!v || 'Benutzername ist erforderlich',
  v => v.length >= 3 || 'Mindestens 3 Zeichen',
  v => /^[a-zA-Z0-9_-]+$/.test(v) || 'Nur Buchstaben, Zahlen, _ und - erlaubt'
]

const emailRules = [
  v => !!v || 'E-Mail ist erforderlich',
  v => /.+@.+\..+/.test(v) || 'Ungültige E-Mail-Adresse'
]

const passwordRules = [
  v => !!v || 'Passwort ist erforderlich',
  v => v.length >= 8 || 'Mindestens 8 Zeichen'
]

const passwordConfirmRules = [
  v => !!v || 'Bitte Passwort bestätigen',
  v => v === password.value || 'Passwörter stimmen nicht überein'
]

// Check if form is valid
const isFormValid = computed(() => {
  return codeValid.value &&
    username.value.length >= 3 &&
    /^[a-zA-Z0-9_-]+$/.test(username.value) &&
    /.+@.+\..+/.test(email.value) &&
    password.value.length >= 8 &&
    password.value === passwordConfirm.value &&
    !isRegistering.value
})

// Initialize on mount
onMounted(async () => {
  // Check if registration is enabled
  const enabled = await referral.checkRegistrationStatus()
  if (!enabled) {
    errorMessage.value = 'Die Selbst-Registrierung ist derzeit deaktiviert.'
    return
  }

  // Get code from URL params or props
  const urlCode = route.params.code || props.code
  if (urlCode) {
    referralCode.value = urlCode
    codeFromUrl.value = true
    await validateCode()
  }
})

// Validate referral code
async function validateCode() {
  if (!referralCode.value) {
    codeValid.value = false
    codeError.value = ''
    campaignName.value = ''
    return
  }

  isValidating.value = true
  codeError.value = ''

  const result = await referral.validateReferralCode(referralCode.value)

  isValidating.value = false

  if (result.valid) {
    codeValid.value = true
    campaignName.value = result.campaign_name || ''
    assignedRole.value = result.role || ''
  } else {
    codeValid.value = false
    codeError.value = result.error || 'Ungültiger Code'
    campaignName.value = ''
  }
}

// Watch for code changes and revalidate
watch(referralCode, () => {
  if (!codeFromUrl.value) {
    codeValid.value = false
    codeError.value = ''
  }
})

// Handle registration
async function handleRegister() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!isFormValid.value) {
    return
  }

  isRegistering.value = true

  try {
    await referral.registerWithReferral({
      referral_code: referralCode.value,
      username: username.value,
      email: email.value,
      password: password.value,
      display_name: displayName.value || username.value
    })

    successMessage.value = 'Registrierung erfolgreich! Du wirst zur Anmeldung weitergeleitet...'

    // Redirect to login after success
    setTimeout(() => {
      router.push({
        path: '/login',
        query: { registered: 'true', username: username.value }
      })
    }, 2000)

  } catch (e) {
    errorMessage.value = e.message || 'Registrierung fehlgeschlagen'
  } finally {
    isRegistering.value = false
  }
}
</script>

<style scoped>
/* Register Page Layout - Fixed viewport, no scroll */
.register-page {
  height: calc(100vh - 94px); /* 64px AppBar + 30px Footer */
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: rgb(var(--v-theme-background));
  overflow: hidden;
}

.register-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 16px;
}

/* Register Card - LLARS Signature Style */
.register-card {
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius);
  box-shadow: var(--llars-shadow-lg, 0 8px 32px rgba(0, 0, 0, 0.12));
  overflow: hidden;
}

/* Header Section */
.register-header {
  background: var(--llars-gradient-primary);
  padding: 24px 20px;
  text-align: center;
  color: white;
}

.register-logo {
  width: 56px;
  height: 56px;
  margin-bottom: 8px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.register-title {
  font-size: 1.35rem;
  font-weight: 600;
  margin: 0 0 2px 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.register-subtitle {
  font-size: 0.85rem;
  margin: 0;
  opacity: 0.9;
}

/* Form Section */
.register-form {
  padding: 20px;
}

.register-field {
  margin-bottom: 12px;
}

.register-field :deep(.v-field) {
  border-radius: var(--llars-radius-sm);
}

.register-button {
  margin-top: 8px;
}

.register-message {
  margin-top: 12px;
  border-radius: var(--llars-radius-xs);
}

/* Footer */
.register-footer {
  padding: 16px 20px;
  text-align: center;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.login-link {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
  font-size: 0.875rem;
  display: inline-flex;
  align-items: center;
  transition: opacity 0.2s ease;
}

.login-link:hover {
  opacity: 0.8;
}

.cursor-pointer {
  cursor: pointer;
}

/* Paint Strokes Background - Same as Login */
.paint-strokes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.paint-strokes div {
  position: absolute;
  filter: blur(55px);
  opacity: 0.55;
}

.paint-strokes div:nth-child(1) {
  background: rgba(176, 202, 151, 0.7);
  top: -24%;
  left: -22%;
  width: 62%;
  height: 56%;
  border-radius: 65% 35% 70% 30% / 55% 45% 60% 40%;
  animation: floatStroke1 26s ease-in-out infinite;
}

.paint-strokes div:nth-child(2) {
  background: rgba(209, 188, 138, 0.6);
  top: -22%;
  right: -24%;
  width: 66%;
  height: 60%;
  border-radius: 40% 60% 55% 45% / 60% 40% 50% 50%;
  animation: floatStroke2 30s ease-in-out infinite;
}

.paint-strokes div:nth-child(3) {
  background: rgba(136, 196, 200, 0.55);
  top: 12%;
  left: -26%;
  width: 56%;
  height: 50%;
  border-radius: 55% 45% 60% 40% / 45% 55% 65% 35%;
  animation: floatStroke3 28s ease-in-out infinite;
}

.paint-strokes div:nth-child(4) {
  background: rgba(232, 200, 122, 0.5);
  top: 12%;
  right: -26%;
  width: 54%;
  height: 56%;
  border-radius: 60% 40% 65% 35% / 35% 65% 45% 55%;
  animation: floatStroke4 32s ease-in-out infinite;
}

.paint-strokes div:nth-child(5) {
  background: rgba(152, 212, 187, 0.6);
  bottom: -24%;
  left: -22%;
  width: 62%;
  height: 56%;
  border-radius: 70% 30% 50% 50% / 50% 50% 70% 30%;
  animation: floatStroke5 27s ease-in-out infinite;
}

.paint-strokes div:nth-child(6) {
  background: rgba(168, 197, 226, 0.55);
  bottom: -22%;
  right: -24%;
  width: 60%;
  height: 62%;
  border-radius: 45% 55% 40% 60% / 40% 60% 70% 30%;
  animation: floatStroke6 34s ease-in-out infinite;
}

.paint-strokes div:nth-child(7) {
  background: rgba(232, 160, 135, 0.45);
  top: -22%;
  left: 4%;
  width: 45%;
  height: 42%;
  border-radius: 35% 65% 45% 55% / 55% 45% 60% 40%;
  animation: floatStroke7 24s ease-in-out infinite;
}

.paint-strokes div:nth-child(8) {
  background: rgba(201, 168, 226, 0.4);
  bottom: -22%;
  left: 52%;
  width: 50%;
  height: 45%;
  border-radius: 45% 55% 35% 65% / 65% 35% 55% 45%;
  animation: floatStroke8 36s ease-in-out infinite;
}

.paint-strokes div:nth-child(9) {
  background: rgba(235, 206, 148, 0.45);
  top: -30%;
  left: 14%;
  width: 72%;
  height: 52%;
  border-radius: 50% 50% 60% 40% / 55% 45% 50% 50%;
  animation: floatStroke9 33s ease-in-out infinite;
}

.paint-strokes div:nth-child(10) {
  background: rgba(180, 210, 240, 0.45);
  bottom: -32%;
  left: 10%;
  width: 78%;
  height: 58%;
  border-radius: 55% 45% 50% 50% / 60% 40% 55% 45%;
  animation: floatStroke10 38s ease-in-out infinite;
}

/* Dark Mode */
.register-page.dark-mode .paint-strokes div {
  filter: blur(80px);
  opacity: 0.35;
}

.register-page.dark-mode .paint-strokes div:nth-child(1) { background: rgba(90, 140, 70, 0.9); }
.register-page.dark-mode .paint-strokes div:nth-child(2) { background: rgba(160, 130, 80, 0.85); }
.register-page.dark-mode .paint-strokes div:nth-child(3) { background: rgba(70, 130, 140, 0.85); }
.register-page.dark-mode .paint-strokes div:nth-child(4) { background: rgba(170, 150, 90, 0.8); }
.register-page.dark-mode .paint-strokes div:nth-child(5) { background: rgba(90, 150, 120, 0.85); }
.register-page.dark-mode .paint-strokes div:nth-child(6) { background: rgba(100, 140, 180, 0.8); }
.register-page.dark-mode .paint-strokes div:nth-child(7) { background: rgba(170, 110, 100, 0.7); }
.register-page.dark-mode .paint-strokes div:nth-child(8) { background: rgba(140, 120, 170, 0.65); }
.register-page.dark-mode .paint-strokes div:nth-child(9) { background: rgba(150, 120, 70, 0.7); }
.register-page.dark-mode .paint-strokes div:nth-child(10) { background: rgba(95, 125, 165, 0.65); }

/* Animations */
@keyframes floatStroke1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(3%, 5%) scale(1.05); }
  66% { transform: translate(-2%, 3%) scale(0.98); }
}
@keyframes floatStroke2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-4%, 3%) scale(1.03); }
  66% { transform: translate(2%, -4%) scale(1.02); }
}
@keyframes floatStroke3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(5%, -3%) scale(1.04); }
  66% { transform: translate(2%, 4%) scale(0.97); }
}
@keyframes floatStroke4 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-3%, 4%) scale(1.02); }
  66% { transform: translate(-5%, -2%) scale(1.05); }
}
@keyframes floatStroke5 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(4%, -4%) scale(1.03); }
  66% { transform: translate(-3%, -2%) scale(0.98); }
}
@keyframes floatStroke6 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-2%, -5%) scale(1.04); }
  66% { transform: translate(3%, 3%) scale(1.01); }
}
@keyframes floatStroke7 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(6%, 4%) scale(1.06); }
  66% { transform: translate(-4%, -3%) scale(0.96); }
}
@keyframes floatStroke8 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-5%, -4%) scale(1.02); }
  66% { transform: translate(4%, 5%) scale(1.04); }
}
@keyframes floatStroke9 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(4%, 3%) scale(1.03); }
  66% { transform: translate(-3%, 2%) scale(0.99); }
}
@keyframes floatStroke10 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-3%, -4%) scale(1.02); }
  66% { transform: translate(4%, 3%) scale(1.03); }
}

/* Mobile Responsive */
.register-page.is-mobile {
  height: 100vh;
  height: 100dvh;
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

.register-page.is-mobile .register-container {
  max-width: 100%;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-page.is-mobile .register-card {
  width: 100%;
  max-width: 380px;
  margin: 0 auto;
}

.register-page.is-ios {
  overscroll-behavior: none;
  -webkit-overflow-scrolling: touch;
}

.register-page.is-ios .register-field :deep(input) {
  font-size: 16px !important;
}

@media (max-width: 600px) {
  .register-page {
    padding: 0;
  }

  .register-container {
    padding: 16px;
    width: 100%;
  }

  .register-header {
    padding: 20px 16px;
  }

  .register-logo {
    width: 48px;
    height: 48px;
  }

  .register-title {
    font-size: 1.2rem;
  }

  .register-form {
    padding: 16px;
  }

  .register-field {
    margin-bottom: 10px;
  }

  .paint-strokes div {
    filter: blur(40px);
    opacity: 0.35;
  }
}

@media (max-width: 380px) {
  .register-header {
    padding: 16px 12px;
  }

  .register-logo {
    width: 40px;
    height: 40px;
  }

  .register-title {
    font-size: 1.1rem;
  }

  .register-form {
    padding: 12px;
  }
}

/* Landscape */
@media (max-height: 600px) and (orientation: landscape) {
  .register-page {
    height: auto;
    min-height: 100vh;
    min-height: 100dvh;
    padding: 16px 0;
    overflow-y: auto;
  }

  .paint-strokes {
    display: none;
  }
}

.register-page {
  overflow-x: hidden;
}
</style>
