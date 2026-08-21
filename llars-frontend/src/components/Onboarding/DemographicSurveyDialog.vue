<template>
  <v-dialog
    :model-value="modelValue"
    persistent
    max-width="640"
    scrollable
    transition="dialog-bottom-transition"
    @update:model-value="(v) => $emit('update:modelValue', v)"
  >
    <div class="demo-survey-card">
      <!-- Decorative header -->
      <div class="demo-survey-header">
        <div class="demo-survey-header__bg" />
        <div class="demo-survey-header__content">
          <div class="demo-survey-icon">
            <LIcon size="32" color="white">mdi-account-question</LIcon>
          </div>
          <div>
            <h2 class="demo-survey-title">{{ $t('onboarding.demographics.title') }}</h2>
            <p class="demo-survey-subtitle">{{ $t('onboarding.demographics.subtitle') }}</p>
          </div>
        </div>
      </div>

      <!-- Body -->
      <div ref="bodyEl" class="demo-survey-body">
        <!-- Gender -->
        <section ref="sectionGender" class="demo-survey-section">
          <div class="demo-survey-question">
            <span class="demo-survey-step">1</span>
            <h3>{{ $t('onboarding.demographics.gender.label') }}</h3>
          </div>
          <LRadioGroup
            v-model="form.gender"
            :options="genderOptions"
            @update:model-value="scrollToNext('age')"
          />
        </section>

        <v-divider class="my-2" />

        <!-- Age -->
        <section ref="sectionAge" class="demo-survey-section">
          <div class="demo-survey-question">
            <span class="demo-survey-step">2</span>
            <h3>{{ $t('onboarding.demographics.age.label') }}</h3>
          </div>
          <LRadioGroup
            v-model="form.age_range"
            :options="ageOptions"
            @update:model-value="scrollToNext('education')"
          />
        </section>

        <v-divider class="my-2" />

        <!-- Education -->
        <section ref="sectionEducation" class="demo-survey-section">
          <div class="demo-survey-question">
            <span class="demo-survey-step">3</span>
            <h3>{{ $t('onboarding.demographics.education.label') }}</h3>
          </div>
          <LRadioGroup
            v-model="form.education"
            :options="educationOptions"
            @update:model-value="scrollToNext('profession')"
          />
        </section>

        <v-divider class="my-2" />

        <!-- Profession (free text, optional) -->
        <section ref="sectionProfession" class="demo-survey-section">
          <div class="demo-survey-question">
            <span class="demo-survey-step">4</span>
            <h3>{{ $t('onboarding.demographics.profession.label') }}</h3>
            <span class="demo-survey-optional">{{ $t('onboarding.demographics.optional') }}</span>
          </div>
          <v-text-field
            v-model="form.profession"
            :placeholder="$t('onboarding.demographics.profession.placeholder')"
            variant="outlined"
            density="comfortable"
            hide-details
            maxlength="255"
            counter
          />
        </section>
      </div>

      <!-- Footer / actions -->
      <div class="demo-survey-footer">
        <div class="demo-survey-progress">
          <span class="demo-survey-progress__label">
            {{ $t('onboarding.demographics.progress', { answered: answeredCount, total: totalCount }) }}
          </span>
          <div class="demo-survey-progress__track">
            <div
              class="demo-survey-progress__bar"
              :style="{ width: progressPercent + '%' }"
            />
          </div>
        </div>

        <div class="demo-survey-actions">
          <LBtn
            variant="text"
            size="small"
            :disabled="submitting"
            @click="skipAll"
          >
            {{ $t('onboarding.demographics.skip') }}
          </LBtn>
          <LBtn
            variant="primary"
            :loading="submitting"
            :disabled="!canSubmit || submitting"
            @click="submit"
          >
            <LIcon class="mr-1">mdi-check</LIcon>
            {{ $t('onboarding.demographics.submit') }}
          </LBtn>
        </div>
      </div>
    </div>
  </v-dialog>
</template>

<script setup>
/**
 * One-time demographic survey shown to users on first login.
 *
 * Once the user submits (or explicitly skips by selecting "no answer"
 * everywhere), we POST to /api/user/demographics. The backend marks the
 * survey completed so this overlay never appears again.
 */
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useSnackbar } from '@/composables/useSnackbar'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  referralLinkId: { type: [Number, String, null], default: null }
})
const emit = defineEmits(['update:modelValue', 'completed'])

const { t } = useI18n()
const { showSuccess, showError } = useSnackbar()

const submitting = ref(false)

// Section refs for the auto-scroll-on-answer flow. After the user picks
// a radio option we slide the next unanswered section into view so they
// don't miss it on shorter viewports where 3-4 questions don't fit.
const bodyEl = ref(null)
const sectionGender = ref(null)
const sectionAge = ref(null)
const sectionEducation = ref(null)
const sectionProfession = ref(null)
const sectionRefs = {
  gender: sectionGender,
  age: sectionAge,
  education: sectionEducation,
  profession: sectionProfession,
}

async function scrollToNext(targetKey) {
  await nextTick()
  const el = sectionRefs[targetKey]?.value
  const container = bodyEl.value
  if (!el || !container) return
  // Position the target near the top of the scroll container so the
  // user clearly sees it's the next unanswered question. 12px top
  // padding matches the section spacing.
  const containerTop = container.getBoundingClientRect().top
  const elTop = el.getBoundingClientRect().top
  const offset = elTop - containerTop - 12
  container.scrollBy({ top: offset, behavior: 'smooth' })
}

const form = reactive({
  gender: null,
  age_range: null,
  education: null,
  profession: ''
})

// Reset on open so re-entries (rare) start clean
watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      form.gender = null
      form.age_range = null
      form.education = null
      form.profession = ''
    }
  }
)

const genderOptions = computed(() => [
  { value: 'female', label: t('onboarding.demographics.gender.female') },
  { value: 'male', label: t('onboarding.demographics.gender.male') },
  { value: 'non_binary', label: t('onboarding.demographics.gender.non_binary') },
  { value: 'no_answer', label: t('onboarding.demographics.no_answer') }
])

const ageOptions = computed(() => [
  { value: 'under_29', label: t('onboarding.demographics.age.under_29') },
  { value: '30_49', label: t('onboarding.demographics.age.30_49') },
  { value: '50_64', label: t('onboarding.demographics.age.50_64') },
  { value: '65_plus', label: t('onboarding.demographics.age.65_plus') },
  { value: 'no_answer', label: t('onboarding.demographics.no_answer') }
])

const educationOptions = computed(() => [
  { value: 'phd', label: t('onboarding.demographics.education.phd') },
  { value: 'master', label: t('onboarding.demographics.education.master') },
  { value: 'bachelor', label: t('onboarding.demographics.education.bachelor') },
  { value: 'vocational', label: t('onboarding.demographics.education.vocational') },
  { value: 'abitur', label: t('onboarding.demographics.education.abitur') },
  { value: 'realschule', label: t('onboarding.demographics.education.realschule') },
  { value: 'no_formal', label: t('onboarding.demographics.education.no_formal') },
  { value: 'no_answer', label: t('onboarding.demographics.no_answer') }
])

const totalCount = 3
const answeredCount = computed(() => {
  let n = 0
  if (form.gender) n++
  if (form.age_range) n++
  if (form.education) n++
  return n
})
const progressPercent = computed(() => Math.round((answeredCount.value / totalCount) * 100))

const canSubmit = computed(() => answeredCount.value === totalCount)

async function postSurvey(payload) {
  submitting.value = true
  try {
    const res = await axios.post('/api/user/demographics', payload)
    if (res.data && res.data.success) {
      emit('completed')
      emit('update:modelValue', false)
      showSuccess(t('onboarding.demographics.thanks'))
    }
  } catch (e) {
    showError(t('onboarding.demographics.errorSave'))
  } finally {
    submitting.value = false
  }
}

function buildPayload(extra = {}) {
  return {
    gender: form.gender,
    age_range: form.age_range,
    education: form.education,
    profession: (form.profession || '').trim() || null,
    referral_link_id: props.referralLinkId ? Number(props.referralLinkId) : null,
    ...extra
  }
}

async function submit() {
  if (!canSubmit.value || submitting.value) return
  await postSurvey(buildPayload())
}

async function skipAll() {
  // Pre-fill any unanswered question with "no answer" — survey stays
  // one-time but we don't force the user to click through.
  if (!form.gender) form.gender = 'no_answer'
  if (!form.age_range) form.age_range = 'no_answer'
  if (!form.education) form.education = 'no_answer'
  await postSurvey(buildPayload())
}
</script>

<style scoped>
.demo-survey-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 92vh;
}

/* Header */
.demo-survey-header {
  position: relative;
  padding: 28px 28px 24px;
  color: #fff;
  overflow: hidden;
}

.demo-survey-header__bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #b0ca97 0%, #88c4c8 60%, #98d4bb 100%);
  z-index: 0;
}

.demo-survey-header__bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 80% -10%, rgba(255, 255, 255, 0.35), transparent 55%),
    radial-gradient(circle at -10% 110%, rgba(255, 255, 255, 0.25), transparent 50%);
}

.demo-survey-header__content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 16px;
}

.demo-survey-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px 4px 12px 4px;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(6px);
  flex-shrink: 0;
}

.demo-survey-title {
  font-size: 1.35rem;
  font-weight: 700;
  margin: 0 0 4px 0;
  letter-spacing: 0.2px;
}

.demo-survey-subtitle {
  font-size: 0.9rem;
  margin: 0;
  opacity: 0.95;
  line-height: 1.4;
}

/* Body */
.demo-survey-body {
  padding: 20px 28px 12px;
  overflow-y: auto;
  flex: 1;
}

.demo-survey-section {
  padding: 12px 0;
}

.demo-survey-question {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.demo-survey-question h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: rgb(var(--v-theme-on-surface));
}

.demo-survey-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 26px;
  padding: 0 8px;
  border-radius: 8px 2px 8px 2px;
  background: rgba(176, 202, 151, 0.25);
  color: #4a6e34;
  font-size: 0.8rem;
  font-weight: 700;
}

.v-theme--dark .demo-survey-step {
  background: rgba(176, 202, 151, 0.18);
  color: #c8e0b0;
}

.demo-survey-optional {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
  font-style: italic;
}

/* Footer */
.demo-survey-footer {
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  padding: 16px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: rgba(176, 202, 151, 0.06);
  flex-wrap: wrap;
}

.v-theme--dark .demo-survey-footer {
  border-top-color: rgba(255, 255, 255, 0.08);
  background: rgba(176, 202, 151, 0.04);
}

.demo-survey-progress {
  flex: 1;
  min-width: 160px;
}

.demo-survey-progress__label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  display: block;
  margin-bottom: 6px;
}

.demo-survey-progress__track {
  width: 100%;
  height: 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.v-theme--dark .demo-survey-progress__track {
  background: rgba(255, 255, 255, 0.08);
}

.demo-survey-progress__bar {
  height: 100%;
  background: linear-gradient(90deg, #b0ca97, #88c4c8);
  transition: width 0.25s ease-out;
}

.demo-survey-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

@media (max-width: 600px) {
  .demo-survey-header {
    padding: 22px 18px 20px;
  }
  .demo-survey-body {
    padding: 16px 18px 8px;
  }
  .demo-survey-footer {
    padding: 14px 18px;
    flex-direction: column;
    align-items: stretch;
  }
  .demo-survey-actions {
    justify-content: flex-end;
  }
}
</style>
