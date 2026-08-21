<template>
  <div class="register-page" :class="{ 'dark-mode': isDarkMode, 'is-mobile': isMobile, 'is-ios': isIOS }">
    <div class="paint-strokes">
      <div v-for="n in 10" :key="n"></div>
    </div>

    <div class="register-container">
      <!-- Auto-redeem panel: an ALREADY logged-in user landed on /join/:code.
           We skip the registration form entirely and redeem the code straight
           away (see autoRedeemForLoggedInUser), then route into the study. -->
      <div v-if="autoRedeeming" class="register-card" data-testid="auto-redeem-panel">
        <div class="register-header">
          <img src="@/assets/logo/llars-logo.png" alt="LLARS Logo" class="register-logo" />
          <h1 class="register-title">{{ $t('auth.joinStudyTitle') }}</h1>
          <p class="register-subtitle">{{ $t('auth.joinStudyLoading') }}</p>
        </div>
        <div class="register-form" data-testid="auto-redeem-loading">
          <v-progress-linear indeterminate color="primary" class="mb-4" />
          <v-alert
            v-if="errorMessage"
            type="error"
            variant="tonal"
            density="compact"
            class="register-message"
          >
            {{ errorMessage }}
          </v-alert>
        </div>
      </div>

      <!-- Registration card. Suppressed once the join was confirmed
           (redeemSucceeded) so the form never flashes behind the persistent
           "Sie sind in der Studie eingetragen" pop-up. -->
      <div v-else-if="!redeemSucceeded" class="register-card">
        <!-- Header with Logo -->
        <div class="register-header">
          <img src="@/assets/logo/llars-logo.png" alt="LLARS Logo" class="register-logo" />
          <h1 class="register-title">{{ $t('auth.registerTitle') }}</h1>
          <p v-if="campaignName" class="register-subtitle">{{ campaignName }}</p>
          <p v-else class="register-subtitle">{{ $t('auth.registerSubtitle') }}</p>
        </div>

        <!-- Registration Form -->
        <div class="register-form" data-testid="register-form">
          <v-form @submit.prevent="handleRegister">
            <!-- Referral Code -->
            <v-text-field
              v-model="referralCode"
              :label="$t('auth.inviteCode')"
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

            <!-- Username + password — only in the "full" signup mode.
                 In "email" / "instant" modes the server generates the
                 credentials, so these fields are hidden entirely. -->
            <template v-if="signupMode === 'full'">
              <!-- Username -->
              <v-text-field
                v-model="username"
                :label="$t('auth.username')"
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
            </template>

            <!-- Email — shown in "full" (per collectEmail flags) and always
                 in "email" mode (where it's the single required identifier).
                 ``collectEmail`` defaults TRUE so manually-typed codes and any
                 non-link-driven registration keep the field in "full" mode. -->
            <v-text-field
              v-if="emailFieldVisible"
              v-model="email"
              :label="emailFieldOptional ? $t('auth.emailOptional') : $t('auth.email')"
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

            <template v-if="signupMode === 'full'">
              <!-- Password -->
              <v-text-field
                v-model="password"
                :label="$t('auth.password')"
                data-testid="password-input"
                autocomplete="new-password"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-lock"
                :type="showPassword ? 'text' : 'password'"
                :disabled="isRegistering"
                :rules="passwordRules"
                :hint="$t('auth.passwordHint')"
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
                :label="$t('auth.passwordConfirm')"
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
            </template>

            <!-- Display Name (Optional) — shown when the link collects it,
                 in "full" and "email" modes (instant collects nothing). -->
            <v-text-field
              v-if="displayNameFieldVisible"
              v-model="displayName"
              :label="$t('auth.displayNameOptional')"
              data-testid="display-name-input"
              autocomplete="name"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-card-account-details"
              :disabled="isRegistering"
              class="register-field"
              hide-details="auto"
            />

            <!--
              Research-study / data-protection consent — classic, always-
              visible required checkbox. No pill, no collapse-behind-a-CTA:
              the consent sits inline in the form on every study / scenario
              referral link. Ticking the box records the grant through the
              same useStudyConsent composable (version + timestamp), so the
              audit-trail recording is unchanged — only the UI is classic.
              The label links to the full data-protection text on
              /study-consent (opens in a new tab).
            -->
            <div v-if="isStudyLink" class="consent-block" data-testid="consent-block">
              <LCheckbox
                :model-value="hasStudyConsent"
                size="small"
                class="consent-checkbox"
                data-testid="consent-mandatory"
                @update:model-value="onConsentToggle"
              >
                <span class="consent-inline-label">
                  {{ $t('auth.consent.classic.checkboxLabel') }}
                  <router-link
                    :to="{ name: 'StudyConsentInfo', query: { return_to: $route.fullPath } }"
                    target="_blank"
                    class="consent-inline-fulltext"
                    data-testid="consent-fulltext-link"
                    @click.stop
                  >
                    {{ $t('auth.consent.classic.fulltextLink') }}
                    <v-icon size="11" class="ml-1">mdi-open-in-new</v-icon>
                  </router-link>
                </span>
              </LCheckbox>
            </div>

            <!--
              Plattform-Zustimmung: Nutzungsbedingungen + Datenschutz. Pflicht
              für JEDE Registrierung (nicht nur Studien-Links). Verlinkt beide
              Rechtstexte (neuer Tab). Der Studien-Consent oben bleibt separat.
            -->
            <div class="consent-block" data-testid="terms-block">
              <LCheckbox
                v-model="termsAccepted"
                size="small"
                class="consent-checkbox"
                data-testid="terms-mandatory"
              >
                <span class="consent-inline-label">
                  <i18n-t keypath="auth.terms.label" scope="global">
                    <template #terms>
                      <router-link
                        to="/Nutzungsbedingungen"
                        target="_blank"
                        class="consent-inline-fulltext"
                        data-testid="terms-link"
                        @click.stop
                      >{{ $t('auth.terms.termsLink') }}</router-link>
                    </template>
                    <template #privacy>
                      <router-link
                        to="/Datenschutz"
                        target="_blank"
                        class="consent-inline-fulltext"
                        data-testid="terms-privacy-link"
                        @click.stop
                      >{{ $t('auth.terms.privacyLink') }}</router-link>
                    </template>
                  </i18n-t>
                </span>
              </LCheckbox>

              <!--
                Transparenz-Hinweis (kein zusätzliches Kontrollkästchen): LLARS
                ist eine Forschungsplattform, eingegebene/Evaluationsdaten werden
                zu Forschungszwecken verarbeitet. Bewusst als Information (nicht
                als erzwungene "Einwilligung"), da die Rechtsgrundlage die
                öffentliche Forschungsaufgabe ist (Art. 6 Abs. 1 lit. e DSGVO),
                nicht eine an die Registrierung gekoppelte Einwilligung.
              -->
              <p class="research-note" data-testid="research-note">
                <v-icon size="14" class="mr-1">mdi-flask-outline</v-icon>
                {{ $t('auth.terms.researchNote') }}
              </p>
            </div>

            <!--
              Optional opt-in: store the email so KI-Zentrum Bayern may contact
              the participant about future studies. Only shown when an email is
              present (collectEmail AND a typed value). Default UNCHECKED (GDPR
              opt-in); never gates registration. Forwarded as
              `store_email_consent` → ReferralRegistration.metadata_json
              (email_contact_consent).
              Deliberately placed BELOW the mandatory terms block: the element
              appears dynamically while the email is being typed, and when it
              sat above the terms checkbox that late insertion shifted the
              layout mid-interaction — clicks aimed at "accept terms" landed on
              this optional marketing opt-in instead (accidental opt-in risk,
              observed in the IJCAI demo E2E run 2026-08-17).
            -->
            <LCheckbox
              v-if="collectEmail && email"
              v-model="storeEmailConsent"
              size="small"
              class="store-email-consent"
              data-testid="store-email-consent"
              :label="$t('auth.storeEmailConsent')"
            />

            <!--
              On study links the button reads "Zustimmen und registrieren".
              Disabled until BOTH the platform terms are accepted AND (on study
              links) the study-consent checkbox is ticked. The hard gates also
              stay inside handleRegister (no consent ⇒ no POST to /register), so
              any other invalid field still surfaces a precise error rather than
              silently doing nothing.
            -->
            <LBtn
              variant="primary"
              block
              size="large"
              @click="handleRegister"
              :loading="isRegistering"
              :disabled="!termsAccepted || (isStudyLink && !hasStudyConsent)"
              :prepend-icon="submitIcon"
              class="register-button"
              data-testid="register-btn"
            >
              {{ submitButtonLabel }}
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
        <!-- Carry the referral code through login so the user returns to
             /join/<code> after authenticating and is then auto-redeemed into
             the study (see autoRedeemForLoggedInUser). Without a code we keep a
             plain /login. Login.vue honours ?redirect=<path> (must start /). -->
        <div class="register-footer">
          <router-link :to="loginLinkTarget" class="login-link" data-testid="login-link">
            <v-icon size="small" class="mr-1">mdi-arrow-left</v-icon>
            {{ $t('auth.loginLink') }}
          </router-link>
        </div>
      </div>

      <!-- Enrollment confirmation pop-up: shown after an already-logged-in user
           redeemed a join link. Confirms study membership, then "Zur Studie"
           routes them into the scenario evaluation (goToStudy). -->
      <v-dialog v-model="redeemSucceeded" max-width="440" persistent>
        <div class="join-success-card">
          <div class="join-success-icon"><LIcon size="44" color="#3f7d6b">mdi-check-circle</LIcon></div>
          <h3 class="join-success-title">{{ $t('auth.joinSuccess.title') }}</h3>
          <p class="join-success-body">{{ $t('auth.joinSuccess.body') }}</p>
          <LBtn variant="primary" prepend-icon="mdi-arrow-right" @click="goToStudy" data-testid="join-success-cta">
            {{ $t('auth.joinSuccess.cta') }}
          </LBtn>
        </div>
      </v-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useI18n } from 'vue-i18n'
import { useMobile } from '@/composables/useMobile'
import { useReferralSystem } from '@/composables/useReferralSystem'
import { useReferralRedeem } from '@/composables/useReferralRedeem'
import { useAuth } from '@/composables/useAuth'
import { useStudyConsent } from '@/composables/useStudyConsent'
import { useLanguage } from '@/composables/useLanguage'

const props = defineProps({
  code: {
    type: String,
    default: ''
  }
})

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)
const { isMobile, isIOS } = useMobile()
const { t, locale } = useI18n()

const router = useRouter()
const route = useRoute()
const referral = useReferralSystem()
const referralRedeem = useReferralRedeem()
const auth = useAuth()
const { setLanguage } = useLanguage()

// Form fields
const referralCode = ref('')
const username = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const displayName = ref('')
const showPassword = ref(false)
// Optional opt-in: may we store the email to contact the user about future
// studies. Default FALSE (GDPR opt-in). Only forwarded when an email is
// actually given — see handleRegister / the v-if on the checkbox.
const storeEmailConsent = ref(false)

// Persist the form across same-tab navigation to /study-consent so
// the user doesn't lose their typed values when they leave to read
// the full Art.13 text and come back. Stored in sessionStorage so it
// dies with the tab — never written to localStorage / cookies / the
// backend. Cleared after a successful register (handleRegister).
const FORM_DRAFT_KEY = 'llars-register-draft'

function readFormDraft() {
  try {
    const raw = sessionStorage.getItem(FORM_DRAFT_KEY)
    return raw ? JSON.parse(raw) : null
  } catch (_) {
    return null
  }
}

function writeFormDraft() {
  try {
    sessionStorage.setItem(FORM_DRAFT_KEY, JSON.stringify({
      referralCode: referralCode.value,
      username: username.value,
      email: email.value,
      password: password.value,
      passwordConfirm: passwordConfirm.value,
      displayName: displayName.value,
      storeEmailConsent: storeEmailConsent.value,
    }))
  } catch (_) { /* sessionStorage unavailable — fail silent */ }
}

function clearFormDraft() {
  try { sessionStorage.removeItem(FORM_DRAFT_KEY) } catch (_) { /* see above */ }
}

// Save on every keystroke (cheap; sessionStorage is in-memory).
watch([referralCode, username, email, password, passwordConfirm, displayName, storeEmailConsent],
  writeFormDraft)

// Research-study consent fully lives on /study-consent. The register
// form reads the persisted snapshot via useStudyConsent and just shows
// a status banner. The three mandatory backend fields are implied =
// true when a snapshot exists at all (granting the snapshot required
// ticking the mandatory checkbox on the consent page).
const CONSENT_VERSION = 'study-consent-v3-2026-05'
const {
  consent: studyConsent,
  clearConsent: clearStudyConsent,
  setConsent: setStudyConsent,
} = useStudyConsent()

// Classic required-checkbox path. Ticking the box records the grant
// through the same useStudyConsent composable (version + client
// timestamp); un-ticking clears it. handleRegister still reads the
// snapshot from useStudyConsent, so the consent recording / audit
// payload is identical to before — only the UI changed from a pill +
// expander to a plain inline checkbox.
function onConsentToggle(checked) {
  if (checked) {
    setStudyConsent({
      version: CONSENT_VERSION,
      granted_at: new Date().toISOString(),
      language: locale.value || 'de',
    })
  } else {
    clearStudyConsent()
  }
}

const hasStudyConsent = computed(() => {
  const c = studyConsent.value
  return !!(c && c.version === CONSENT_VERSION)
})

// State
const isValidating = ref(false)
const isRegistering = ref(false)
const codeValid = ref(false)
const codeError = ref('')
const campaignName = ref('')
const assignedRole = ref('')
const isStudyLink = ref(false)

// Plattform-Zustimmung zu Nutzungsbedingungen + Datenschutzerklärung —
// verpflichtend für JEDE Registrierung, unabhängig von Studien-Links. Bewusst
// NICHT persistiert: die Zustimmung wird pro Registrierungsvorgang aktiv
// gesetzt. Der Studien-Consent (useStudyConsent) bleibt davon getrennt und gilt
// zusätzlich bei Studien-Links (dort zwei Häkchen: Plattform + Studie).
const termsAccepted = ref(false)
// Form-shape toggles from the validated referral link. Default TRUE
// keeps the field visible for any non-link-driven registration so a
// user who types in a code manually still sees the email+name fields.
const collectEmail = ref(true)
const collectDisplayName = ref(true)
// When collectEmail is TRUE, this decides whether the email field is
// optional (shown but skippable). Default FALSE keeps email required.
const collectEmailOptional = ref(false)
// Per-referral-link signup shape from the validated code:
//   'full'    — username + password + (email per collect flags) + display name
//   'email'   — ONLY email (required) + optional display name; server mints
//               username + password.
//   'instant' — no inputs at all, just a single action button; server mints
//               everything (and a placeholder email).
// Defaults to 'full' so older backends / manually-typed codes keep the
// classic registration form.
const signupMode = ref('full')
const errorMessage = ref('')
const successMessage = ref('')
const codeFromUrl = ref(false)
// True while an already-authenticated visitor's referral code is being
// auto-redeemed (we hide the registration form and show a brief loader).
const autoRedeeming = ref(false)
// Enrollment-confirmation pop-up shown after a logged-in user redeems a join
// link ("Sie sind in der Studie eingetragen" → "Zur Studie" routes them in).
const redeemSucceeded = ref(false)
const redeemTargetPath = ref('')

function goToStudy() {
  redeemSucceeded.value = false
  router.push(redeemTargetPath.value || '/Home')
}

// Login link target: when the page carries a referral code, route through
// login back to /join/<code> so the user returns here authenticated and gets
// auto-redeemed into the study. Otherwise a plain /login.
const loginLinkTarget = computed(() => {
  const code = (referralCode.value || route.params.code || props.code || '').trim()
  return code
    ? { path: '/login', query: { redirect: `/join/${code}` } }
    : '/login'
})

// --- signup_mode-driven UI shape -----------------------------------------
// Email field: visible in 'email' mode (always — it's the sole identifier)
// and in 'full' mode when the link collects an email. Never in 'instant'.
const emailFieldVisible = computed(() =>
  signupMode.value === 'email' || (signupMode.value === 'full' && collectEmail.value)
)
// In 'email' mode the address is mandatory; in 'full' mode it follows the
// collectEmailOptional flag.
const emailFieldOptional = computed(() =>
  signupMode.value === 'full' && collectEmailOptional.value
)
// Display name follows the collect flag, but never appears in 'instant' mode
// (which collects nothing at all).
const displayNameFieldVisible = computed(() =>
  signupMode.value !== 'instant' && collectDisplayName.value
)

// Submit button label/icon per mode. Study links keep the "agree and
// register" wording (consent gate), otherwise each mode gets its own CTA.
const submitButtonLabel = computed(() => {
  if (isStudyLink.value) return t('auth.consent.classic.submitButton')
  if (signupMode.value === 'instant') return t('auth.signupModes.instantButton')
  if (signupMode.value === 'email') return t('auth.signupModes.emailButton')
  return t('auth.register')
})
const submitIcon = computed(() =>
  signupMode.value === 'instant' ? 'mdi-rocket-launch' : 'mdi-account-plus'
)

// Validation rules
const usernameRules = [
  v => !!v || t('validation.required'),
  v => v.length >= 3 || t('validation.minLength', { min: 3 }),
  v => /^[a-zA-Z0-9_-]+$/.test(v) || t('auth.validation.usernamePattern')
]

// Email rules depend on the link's form-shape flags and signup mode. When
// the field is hidden it has no rules; when optional, a blank value passes
// but a typed value must be well-formed; otherwise it's required + validated.
// In 'email' mode the field is always required (sole identifier).
const emailRules = computed(() => {
  if (!emailFieldVisible.value) return []
  if (emailFieldOptional.value) {
    return [v => !v || /.+@.+\..+/.test(v) || t('validation.invalidEmail')]
  }
  return [
    v => !!v || t('validation.required'),
    v => /.+@.+\..+/.test(v) || t('validation.invalidEmail')
  ]
})

const passwordRules = [
  v => !!v || t('validation.required'),
  v => v.length >= 8 || t('validation.minLength', { min: 8 })
]

const passwordConfirmRules = [
  v => !!v || t('validation.required'),
  v => v === password.value || t('auth.validation.passwordMismatch')
]

// Form is valid only when (a) the per-mode field rules pass and (b) for
// study referrals, a granted consent snapshot exists in useStudyConsent
// state (granted on /study-consent). Validation is per signup_mode:
//   'instant' — nothing to validate (just the consent gate on study links).
//   'email'   — a well-formed email is required; no username/password.
//   'full'    — classic: username + password (+ email per collect flags).
const isFormValid = computed(() => {
  if (isRegistering.value) return false
  if (!codeValid.value) return false

  // Plattform-Bedingungen (Nutzungsbedingungen + Datenschutz) müssen für jede
  // Registrierung akzeptiert sein.
  if (!termsAccepted.value) return false

  // Study consent gate applies to every mode.
  const consentOk = !isStudyLink.value || hasStudyConsent.value
  if (!consentOk) return false

  if (signupMode.value === 'instant') {
    // No inputs — consent (if any) is the only requirement.
    return true
  }

  if (signupMode.value === 'email') {
    // Email is the sole required identifier and must be well-formed.
    return /.+@.+\..+/.test(email.value)
  }

  // 'full' (default): classic validation. Email check only when the link
  // both demands an email AND makes it required; otherwise the backend
  // synthesizes a placeholder address.
  const emailOk = !collectEmail.value || collectEmailOptional.value || /.+@.+\..+/.test(email.value)
  return username.value.length >= 3 &&
    /^[a-zA-Z0-9_-]+$/.test(username.value) &&
    emailOk &&
    password.value.length >= 8 &&
    password.value === passwordConfirm.value
})

// Initialize on mount
onMounted(async () => {
  // Restore any draft the user left when navigating away to read
  // /study-consent (or any other same-tab back-and-forth). Done
  // BEFORE the URL-code restore so a fresh /join/:code link still
  // wins over any stale draft.
  const draft = readFormDraft()
  if (draft) {
    if (draft.username) username.value = draft.username
    if (draft.email) email.value = draft.email
    if (draft.password) password.value = draft.password
    if (draft.passwordConfirm) passwordConfirm.value = draft.passwordConfirm
    if (draft.displayName) displayName.value = draft.displayName
    if (draft.storeEmailConsent) storeEmailConsent.value = draft.storeEmailConsent === true
    // Don't restore referralCode from the draft when the URL already
    // carries one — the URL is authoritative.
  }

  // Already logged in + a referral code in the URL → don't show the
  // registration form at all. Auto-redeem the code and route straight into
  // the study's evaluation. This is the "existing account + referral link"
  // entry point (after returning here from login, or following a shared link
  // while signed in). Done BEFORE the registration-enabled gate because an
  // existing user joining a study doesn't depend on public signups being open.
  const urlCode = route.params.code || props.code
  if (urlCode && auth.isAuthenticated.value) {
    referralCode.value = urlCode
    await autoRedeemForLoggedInUser(urlCode)
    return
  }

  // Check if registration is enabled
  const enabled = await referral.checkRegistrationStatus()
  if (!enabled) {
    errorMessage.value = t('auth.errors.registrationDisabled')
    return
  }

  // Get code from URL params or props
  if (urlCode) {
    referralCode.value = urlCode
    codeFromUrl.value = true
    await validateCode()
  } else if (draft?.referralCode) {
    // Fallback: typed-in code from the draft (no URL code present)
    referralCode.value = draft.referralCode
    await validateCode()
  }
})

/**
 * Auto-redeem a referral code for an ALREADY-authenticated visitor and route
 * them into the study's evaluation.
 *
 * Flow: POST /api/referral/redeem (via useReferralRedeem) → on success route to
 * /scenarios/<target_scenario_id>/evaluate. Idempotent on the backend, so an
 * `already_enrolled` response still routes the user into the evaluation
 * (they're a member already — exactly where we want them). On error we surface
 * the backend message briefly and fall back to /Home so the user is never stuck
 * on a blank form they don't need.
 */
async function autoRedeemForLoggedInUser(code) {
  autoRedeeming.value = true
  errorMessage.value = ''

  const { success, data, error } = await referralRedeem.redeem(code)

  if (success && (data?.redirect_path || data?.target_scenario_id)) {
    // Newly enrolled OR already a member → confirm with a clear pop-up
    // ("Sie sind in der Studie eingetragen"), then into the evaluation via the
    // dialog's "Zur Studie" button (goToStudy). Multi-scenario links land on the
    // hub (/evaluation); single-scenario links go straight into the scenario.
    redeemTargetPath.value = data.redirect_path
      || `/scenarios/${data.target_scenario_id}/evaluate`
    autoRedeeming.value = false
    redeemSucceeded.value = true
    return
  }

  if (success) {
    // Redeemed but the link has no target scenario to land in — send the user
    // home rather than leaving them on the auto-redeem loader.
    router.push('/Home')
    return
  }

  // Failure: show the human-readable message, then fall back Home. Keep the
  // loader card visible so the error is readable before we navigate away.
  errorMessage.value = error && error !== 'request_failed'
    ? error
    : t('auth.errors.joinFailed')
  router.push('/Home')
}

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
    // Per-referral-link default UI language. The backend tags each link
    // with a default_locale (e.g. the IJCAI link is English, others
    // German). Apply it so the pre-login /join page renders in the link's
    // language; setLanguage persists to localStorage, so the post-signup
    // session stays in it. Guarded to the two supported locales.
    if (result.default_locale === 'de' || result.default_locale === 'en') {
      setLanguage(result.default_locale)
    }
    // Pick up the form-shape toggles from the backend. Defaults TRUE
    // when the response is missing the keys (old backends, manually-
    // typed codes) so existing flows keep email+name visible.
    collectEmail.value = result.collect_email !== false
    collectDisplayName.value = result.collect_display_name !== false
    // Optional-email flag only matters when collectEmail is TRUE. Default
    // FALSE keeps the email field required for older backends / typed codes.
    collectEmailOptional.value = result.collect_email_optional === true
    // Per-link signup shape. Only the three known modes are honoured;
    // anything else (or a missing value from an older backend) falls back
    // to the classic 'full' form.
    signupMode.value = ['full', 'email', 'instant'].includes(result.signup_mode)
      ? result.signup_mode
      : 'full'
    // Study-consent gate. The backend is authoritative: ``is_study`` is
    // true for study-pattern slugs/labels AND for any scenario-bound
    // referral-join (e.g. /join/kann-ki-beratung-digi-sucht). The slug/
    // label heuristic is kept only as a fallback for older backends whose
    // validate response carries no ``is_study`` / ``target_scenario_id``.
    const slug = (result.slug || referralCode.value || '').toLowerCase()
    const label = (result.label || result.campaign_name || '').toLowerCase()
    const heuristic = slug.startsWith('human_comparison_') ||
      slug.startsWith('study_') ||
      slug.startsWith('emnlp-') ||
      label.includes('study') ||
      label.includes('emnlp')
    isStudyLink.value = result.is_study === true ||
      result.target_scenario_id != null ||
      heuristic
  } else {
    codeValid.value = false
    codeError.value = result.error || t('auth.errors.invalidCode')
    campaignName.value = ''
    isStudyLink.value = false
    signupMode.value = 'full'

    // When the user lands via /join/:code with an invalid code, send
    // them to a dedicated explainer page instead of trying to recover
    // the form. The attempted code is carried over for context.
    if (codeFromUrl.value) {
      router.replace({
        name: 'JoinInvalid',
        query: { code: referralCode.value || '' },
      })
    }
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

  // Hard gate: never POST without a granted study consent on study
  // referrals. The button stays clickable so we surface the precise
  // reason here. The pill itself links to /study-consent — clicking
  // the error message could also nudge them there, but keeping the
  // pill's CTA the single source of navigation avoids two ways to
  // do the same thing.
  if (isStudyLink.value && !hasStudyConsent.value) {
    errorMessage.value = t('auth.errors.consentRequired')
    return
  }

  // Verpflichtende Zustimmung zu Nutzungsbedingungen + Datenschutz für jede
  // Registrierung — eigener Hard-Gate, damit der Grund präzise angezeigt wird.
  if (!termsAccepted.value) {
    errorMessage.value = t('auth.errors.termsRequired')
    return
  }

  if (!isFormValid.value) {
    errorMessage.value = t('auth.errors.formIncomplete')
    return
  }

  isRegistering.value = true

  try {
    // Audit-trail payload pulled straight from the persisted study
    // consent snapshot (sessionStorage via useStudyConsent). The
    // snapshot only exists because the user ticked the mandatory
    // checkbox, so participation is implied.
    //
    // We send both shapes: the new single `participation:true` AND the
    // legacy three-key mirror (study_participation /
    // data_storage_pseudonymized / research_publication). This keeps
    // the frontend working against ANY backend version — production
    // < v3 only checks the legacy keys; v3+ accepts either. The
    // backend mirror writes them to the legacy keys anyway so
    // downstream queries don't need to change.
    const snap = studyConsent.value
    const consentPayload = isStudyLink.value && snap ? {
      version: snap.version || CONSENT_VERSION,
      participation: true,
      study_participation: true,
      data_storage_pseudonymized: true,
      research_publication: true,
      granted_at_client: snap.granted_at || null,
    } : null
    // The locale forwarded with the registration (used by instant/email
    // modes too, where there's no consent block to carry it).
    const localeShort = (typeof navigator !== 'undefined' && navigator.language)
      ? navigator.language.slice(0, 2)
      : 'en'

    // Payload shape is driven by signup_mode (see the field-visibility
    // computeds). The backend mints whatever the link omits:
    //   'instant' — ONLY { referral_code, consent?, locale }. No
    //               username/email/password (all server-generated).
    //   'email'   — ONLY email (+ display name / consent). Server mints
    //               username + password. NEVER send username/password.
    //   'full'    — classic: username + password (+ email per collect flags).
    let payloadBody
    if (signupMode.value === 'instant') {
      payloadBody = {
        referral_code: referralCode.value,
        ...(consentPayload ? { consent: consentPayload } : {}),
        locale: localeShort,
      }
    } else if (signupMode.value === 'email') {
      payloadBody = {
        referral_code: referralCode.value,
        email: email.value,
        // Only meaningful alongside a real email — backend stores it in
        // metadata_json.email_contact_consent for re-contact filtering.
        store_email_consent: storeEmailConsent.value === true,
        ...(collectDisplayName.value && displayName.value ? { display_name: displayName.value } : {}),
        ...(consentPayload ? { consent: consentPayload } : {}),
        locale: localeShort,
      }
    } else {
      // 'full': classic. Only forward email + display name when the link
      // demanded them. The backend synthesizes a placeholder address when
      // collect_email is false; display name defaults to the username.
      payloadBody = {
        referral_code: referralCode.value,
        username: username.value,
        password: password.value,
        ...(collectEmail.value && email.value ? {
          email: email.value,
          store_email_consent: storeEmailConsent.value === true,
        } : {}),
        ...(collectDisplayName.value && displayName.value ? { display_name: displayName.value } : {}),
        ...(consentPayload ? { consent: consentPayload, locale: localeShort } : {}),
      }
    }

    const response = await referral.registerWithReferral(payloadBody)

    // Snapshot has done its job — flush it so a second register on the
    // same tab doesn't accidentally inherit the previous user's consent.
    if (isStudyLink.value) clearStudyConsent()
    // Same reasoning for the form-draft: never let the next user on
    // this tab see the previous credentials prefilled.
    clearFormDraft()

    successMessage.value = t('auth.messages.registrationSuccess')

    const payload = response?.data || response || {}

    // Returning email-mode user: the backend emailed a one-time sign-in link
    // (email-ownership proof) instead of logging them in. Show "check your
    // email" and stop — no auto-login, no redirect.
    if (payload.verification_sent) {
      successMessage.value = payload.message || t('auth.messages.registrationSuccess')
      return
    }

    const targetScenarioId = payload.target_scenario_id
    // The username may have been generated server-side ('email'/'instant'
    // modes), so prefer the one echoed in the response over the local field
    // (which is empty in those modes).
    const resolvedUsername = payload.username || username.value

    // Auto-login: backend now mints an Authentik token bundle in the
    // register response. If present, install it directly and redirect
    // straight into the scenario — saves the user a second password prompt
    // on top of the registration form. Falls back to the classic /login
    // redirect if the token wasn't returned (Authentik briefly
    // unreachable, etc.).
    // Prefer the server-computed landing path: exactly 1 scenario -> straight
    // into it, more than 1 -> the evaluation hub (/evaluation). Fall back to the
    // legacy single-scenario / home behaviour.
    const target = payload.redirect_path
      || (targetScenarioId ? `/scenarios/${targetScenarioId}/evaluate` : '/Home')

    if (payload.auto_login && payload.token) {
      try {
        const ok = await auth.applyTokenBundle(payload.token, resolvedUsername)
        if (ok) {
          setTimeout(() => router.push(target), 600)
          return
        }
      } catch (e) {
        // fall through to classic redirect
      }
    }

    const loginQuery = { registered: 'true', username: resolvedUsername }
    if (target && target !== '/Home') loginQuery.redirect = target
    setTimeout(() => router.push({ path: '/login', query: loginQuery }), 2000)

  } catch (e) {
    errorMessage.value = e.message || t('auth.errors.registrationFailed')
  } finally {
    isRegistering.value = false
  }
}
</script>

<style scoped>
/* Classic, always-visible consent block: a framed inline panel holding
   the required checkbox. Uses the LLARS asymmetric border-radius and a
   subtle primary tint so it reads as part of the form, not an alert. */
.consent-block {
  margin-top: 12px;
  padding: 12px 14px;
  border: 1px solid rgba(var(--v-theme-primary), 0.35);
  border-radius: 12px 4px 12px 4px;
  background: rgba(var(--v-theme-primary), 0.05);
}

/* Forschungs-Transparenzhinweis unter der Zustimmungs-Checkbox — dezent,
   informativ (kein Kontrollkästchen). */
.research-note {
  display: flex;
  align-items: flex-start;
  gap: 2px;
  margin: 10px 0 0;
  font-size: 0.78rem;
  line-height: 1.45;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Optional email-storage opt-in — a lighter padded box below the mandatory
   consent box, so the multi-line label has room and the two align. */
.store-email-consent {
  margin-top: 10px;
  padding: 10px 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 12px 4px 12px 4px;
  background: rgba(var(--v-theme-on-surface), 0.03);
}
.store-email-consent :deep(.l-checkbox__label),
.store-email-consent :deep(label) {
  line-height: 1.45;
}

/* Inline link to the full data-protection text, sitting in the label. */
.consent-inline-fulltext {
  display: inline-flex;
  align-items: center;
  color: rgb(var(--v-theme-primary));
  font-weight: 500;
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
  white-space: nowrap;
}

.consent-inline-fulltext:hover,
.consent-inline-fulltext:focus-visible {
  text-decoration-thickness: 2px;
  outline: none;
}

.consent-inline-label {
  font-size: 0.8rem;
  line-height: 1.45;
}

/* Keep the checkbox + multi-line label top-aligned so the box sits next
   to the first line of the wrapping consent text. */
.consent-checkbox {
  align-items: flex-start;
}

/* Full data-protection text — only shown inside the modal dialog. */
.consent-info-dialog .consent-info-content {
  font-size: 0.85rem;
  line-height: 1.55;
}

.consent-info-dialog .consent-info-content p {
  margin: 0 0 10px 0;
}

.consent-info-dialog .consent-intro {
  font-size: 0.85rem;
  margin-bottom: 12px;
  opacity: 0.9;
  line-height: 1.45;
}

.consent-info-dialog .consent-footer {
  font-size: 0.78rem;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.7;
  margin-top: 14px;
  line-height: 1.45;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  padding-top: 10px;
}

/* Register Page Layout.
   Page is naturally sized by its content: when the card fits in the
   available viewport (AppBar + Footer subtracted) it sits centered
   and the page does NOT scroll. When the card grows past that —
   consent block shown, error message shown, narrow viewport —
   the document scrolls organically, no scrollbar pre-rendered. */
.register-page {
  /* min-height pins the page to the available viewport so the card
     stays vertically centered on tall screens; content above this
     threshold expands the page and the document scroll kicks in. */
  min-height: calc(100vh - 94px); /* 64px AppBar + 30px Footer */
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: rgb(var(--v-theme-background));
  /* No overflow-y declaration → inherits `visible`; the *document*
     scrolls when content overflows, not the page container. That
     keeps the scrollbar from rendering when nothing overflows. */
}

.register-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  /* Vertical padding gives breathing room above/below the card when
     the document does scroll. */
  padding: 24px 16px;
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

/* Enrollment-confirmation pop-up (logged-in user redeemed a join link). */
.join-success-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
  padding: 28px 24px 24px;
  background: rgb(var(--v-theme-surface));
  border-radius: 16px 4px 16px 4px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}
.join-success-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(152, 212, 187, 0.18);
}
.join-success-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}
.join-success-body {
  margin: 0;
  font-size: 0.92rem;
  line-height: 1.5;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.85;
}

/* Paint Strokes Background.
   ``overflow: hidden`` clips the absolutely-positioned strokes inside
   their own container so they can keep their negative offsets / large
   widths without triggering a document-level scrollbar. The page
   itself stays free to scroll vertically only when its content
   actually overflows the viewport. */
.paint-strokes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
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
