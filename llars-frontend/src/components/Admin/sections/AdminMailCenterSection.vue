<template>
  <div class="admin-mail-center">
    <p class="text-body-2 text-medium-emphasis mb-4">
      {{ $t('admin.mailCenter.intro') }}
    </p>

    <LTabs v-model="tab" :tabs="tabs" class="mb-4" />

    <!-- ========================= VORLAGEN / TEMPLATES ========================= -->
    <div v-if="tab === 'templates'">
      <LCard
        :title="$t('admin.mailCenter.templates.title')"
        icon="mdi-email-multiple-outline"
        class="mb-4"
      >
        <template #actions>
          <LBtn variant="text" size="small" prepend-icon="mdi-refresh" @click="loadTemplates">
            {{ $t('admin.mailCenter.templates.refresh') }}
          </LBtn>
        </template>

        <p class="text-body-2 text-medium-emphasis mb-2">
          {{ $t('admin.mailCenter.templates.help') }}
        </p>
        <LTag variant="info" size="sm" class="mb-4">
          <v-icon size="14" class="mr-1">mdi-flask-outline</v-icon>
          {{ $t('admin.mailCenter.templates.sampleNote') }}
        </LTag>

        <LLoading v-if="templatesLoading" :text="$t('common.loading')" />

        <!-- ===== Full-width sliding gallery (iPad-landscape cover-flow vibe) =====
             One prominent slide fills the available width with a peek of the
             neighbours (margins are inset so the next/prev slide shows at the
             edges). Slides scroll-snap horizontally; prev/next arrows scroll by
             exactly one slide; the dot rail jumps to any slide. Both the system
             templates and the branded study invitations live in the SAME track
             — recruitment slides carry a "Studie" badge to set them apart. -->
        <div v-else class="template-slider">
          <!-- Prev / Next arrows (hidden when there's nothing to scroll). -->
          <LIconBtn
            v-if="slides.length > 1"
            class="slider-arrow slider-arrow--prev"
            icon="mdi-chevron-left"
            :tooltip="$t('admin.mailCenter.templates.prev')"
            :disabled="activeSlide === 0"
            @click="scrollSlides(-1)"
          />

          <!-- Snap track: each slide is an isolated, full-document mail iframe. -->
          <div ref="trackRef" class="slider-track" @scroll="onTrackScroll">
            <div
              v-for="(slide, i) in slides"
              :key="slide.key"
              class="slider-slide"
              :class="{ 'slider-slide--active': i === activeSlide }"
            >
              <LCard
                class="slide-card"
                :title="slide.label"
                :icon="slide.icon"
                variant="outlined"
              >
                <template #actions>
                  <!-- Recruitment slides are tagged "Studie"; system templates
                       keep their existing colour-coded type tag. -->
                  <LTag :variant="slide.recruitment ? 'accent' : slide.variant" size="sm">
                    {{ slide.recruitment ? $t('admin.mailCenter.templates.studyBadge') : slide.label }}
                  </LTag>
                </template>

                <p v-if="slide.description" class="text-caption text-medium-emphasis mb-2">{{ slide.description }}</p>
                <div v-if="slide.variables && slide.variables.length" class="mb-2">
                  <span class="text-caption font-weight-medium">{{ $t('admin.mailCenter.templates.variables') }}:</span>
                  <LTag
                    v-for="v in slide.variables"
                    :key="v"
                    variant="secondary"
                    size="sm"
                    class="ml-1"
                  >{{ v }}</LTag>
                </div>
                <div class="mb-2">
                  <strong class="text-caption">{{ $t('admin.mailCenter.preview.subject') }}:</strong>
                  <span class="text-caption">{{ slide.subject }}</span>
                </div>
                <!-- Render the mail in an isolated iframe so its full-document
                     HTML + inline styles don't leak into / get mangled by the
                     admin page (v-html into a div breaks the branded layout). -->
                <iframe
                  class="mail-preview-iframe slide-iframe"
                  :srcdoc="slide.html"
                  sandbox=""
                  loading="lazy"
                  :title="slide.label"
                ></iframe>
                <div class="d-flex justify-end align-center mt-2" style="gap: 8px;">
                  <LBtn
                    variant="text"
                    size="small"
                    prepend-icon="mdi-fullscreen"
                    @click="openFullscreen(slide.html, slide.label, slide.subject)"
                  >
                    {{ $t('admin.mailCenter.preview.fullscreen') }}
                  </LBtn>
                  <!-- Quick send: reveal an inline address field for THIS card and
                       ship the template to the entered address. -->
                  <LBtn
                    variant="primary"
                    size="small"
                    prepend-icon="mdi-send-variant-outline"
                    @click="toggleQuickSend(slide)"
                  >
                    {{ $t('admin.mailCenter.quickSend.button') }}
                  </LBtn>
                </div>

                <!-- Inline quick-send panel (per card) -->
                <div v-if="quickSendKey === slide.key" class="quick-send-panel mt-3">
                  <v-text-field
                    v-model="quickSendEmail"
                    :label="$t('admin.mailCenter.quickSend.placeholder')"
                    type="email"
                    variant="outlined"
                    density="compact"
                    hide-details
                    autofocus
                    prepend-inner-icon="mdi-email-outline"
                    @keyup.enter="doQuickSend(slide)"
                  />
                  <div class="d-flex justify-end align-center mt-2" style="gap: 8px;">
                    <LBtn variant="cancel" size="small" @click="quickSendKey = null">
                      {{ $t('admin.mailCenter.quickSend.cancel') }}
                    </LBtn>
                    <LBtn
                      variant="primary"
                      size="small"
                      prepend-icon="mdi-send"
                      :loading="quickSendLoading"
                      :disabled="!quickSendEmail.trim()"
                      @click="doQuickSend(slide)"
                    >
                      {{ $t('admin.mailCenter.quickSend.send') }}
                    </LBtn>
                  </div>
                </div>
              </LCard>
            </div>
          </div>

          <LIconBtn
            v-if="slides.length > 1"
            class="slider-arrow slider-arrow--next"
            icon="mdi-chevron-right"
            :tooltip="$t('admin.mailCenter.templates.next')"
            :disabled="activeSlide >= slides.length - 1"
            @click="scrollSlides(1)"
          />

          <!-- Recruitment hint + clickable dot/position rail. The active dot is
               highlighted; recruitment dots get an accent tint so the study
               block is visible at a glance in the rail. -->
          <div v-if="slides.length > 1" class="slider-dots">
            <button
              v-for="(slide, i) in slides"
              :key="`dot-${slide.key}`"
              type="button"
              class="slider-dot"
              :class="{
                'slider-dot--active': i === activeSlide,
                'slider-dot--recruitment': slide.recruitment,
              }"
              :aria-label="$t('admin.mailCenter.templates.goToSlide', { n: i + 1 })"
              @click="goToSlide(i)"
            ></button>
          </div>
        </div>

        <!-- Caption explaining the study-invitation block in the gallery. -->
        <p class="text-caption text-medium-emphasis mt-3">
          <v-icon size="14" class="mr-1">mdi-account-multiple-plus</v-icon>
          <strong>{{ $t('admin.mailCenter.templates.recruitmentHeader') }}:</strong>
          {{ $t('admin.mailCenter.templates.recruitmentNote') }}
        </p>
      </LCard>
    </div>

    <!-- ========================= SENDEN / COMPOSE ========================= -->
    <!-- Side-by-side: composer form (left) | live preview (right), with the
         LLARS vertical resizer. Fits one screen; each pane scrolls on its own. -->
    <div v-else-if="tab === 'compose'" class="compose-split" ref="containerRef">
      <!-- LEFT: composer form -->
      <div class="compose-pane compose-form-pane" :style="leftPanelStyle()">
      <LCard :title="$t('admin.mailCenter.composer.title')" icon="mdi-email-edit-outline" class="mb-4">
        <!-- Mode toggle -->
        <v-btn-toggle v-model="mode" mandatory density="comfortable" color="primary" class="mb-4">
          <v-btn value="invitation" prepend-icon="mdi-account-multiple-plus">
            {{ $t('admin.mailCenter.mode.invitation') }}
          </v-btn>
          <v-btn value="announcement" prepend-icon="mdi-bullhorn">
            {{ $t('admin.mailCenter.mode.announcement') }}
          </v-btn>
        </v-btn-toggle>

        <!-- Invitation fields -->
        <template v-if="mode === 'invitation'">
          <v-select
            v-model="form.referralLinkId"
            :items="linkOptions"
            item-title="label"
            item-value="value"
            :label="$t('admin.mailCenter.composer.referralLink')"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />
          <!-- Branded template picked → edit its raw HTML directly. Otherwise
               keep the generic intro field (generic render on send/preview). -->
          <template v-if="selectedBrandedTemplate">
            <LTag variant="accent" size="sm" class="mb-3">
              <v-icon size="14" class="mr-1">mdi-palette-swatch</v-icon>
              {{ $t('admin.mailCenter.composer.brandedBadge', { org: selectedBrandedTemplate.org }) }}
            </LTag>
            <v-textarea
              v-model="invitationBodyHtml"
              :label="$t('admin.mailCenter.composer.templateBody')"
              :hint="$t('admin.mailCenter.composer.templateBodyHint')"
              variant="outlined"
              density="comfortable"
              rows="14"
              class="mb-3 template-html-editor"
              spellcheck="false"
            />
          </template>
          <v-textarea
            v-else
            v-model="form.intro"
            :label="$t('admin.mailCenter.composer.intro')"
            :hint="$t('admin.mailCenter.composer.introHint')"
            variant="outlined"
            density="comfortable"
            rows="2"
            class="mb-3"
          />
        </template>

        <!-- Announcement fields -->
        <template v-else>
          <v-text-field
            v-model="form.subject"
            :label="$t('admin.mailCenter.composer.subject')"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />
          <v-textarea
            v-model="form.body"
            :label="$t('admin.mailCenter.composer.body')"
            :hint="$t('admin.mailCenter.composer.bodyHint')"
            variant="outlined"
            density="comfortable"
            rows="6"
            class="mb-3"
          />
        </template>
      </LCard>

      <!-- Recipient selector -->
      <LCard :title="$t('admin.mailCenter.recipients.title')" icon="mdi-account-multiple" class="mb-4">
        <p class="text-caption text-medium-emphasis mb-3">
          {{ $t('admin.mailCenter.recipients.help') }}
        </p>

        <v-textarea
          v-model="recipients.listText"
          :label="$t('admin.mailCenter.recipients.addresses')"
          :hint="$t('admin.mailCenter.recipients.addressesHint')"
          variant="outlined"
          density="comfortable"
          rows="3"
          class="mb-3"
        />

        <!-- Announcement-only: resolve by link / scenario / role -->
        <template v-if="mode === 'announcement'">
          <v-row dense>
            <v-col cols="12" md="4">
              <v-select
                v-model="recipients.referralLinkId"
                :items="[{ label: $t('admin.mailCenter.recipients.none'), value: null }, ...linkOptions]"
                item-title="label"
                item-value="value"
                :label="$t('admin.mailCenter.recipients.byLink')"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field
                v-model.number="recipients.scenarioId"
                :label="$t('admin.mailCenter.recipients.byScenario')"
                type="number"
                variant="outlined"
                density="comfortable"
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-select
                v-model="recipients.roleName"
                :items="roleOptions"
                :label="$t('admin.mailCenter.recipients.byRole')"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </v-col>
          </v-row>
        </template>
        <template v-else>
          <p class="text-caption text-medium-emphasis">
            {{ $t('admin.mailCenter.recipients.inviteLinkNote') }}
          </p>
        </template>
      </LCard>

      <!-- Actions (the preview is now always-on in the right pane) -->
      <div class="d-flex align-center flex-wrap" style="gap: 12px;">
        <LBtn
          variant="primary"
          prepend-icon="mdi-send"
          :disabled="!canSend"
          @click="confirmSend = true"
        >
          {{ $t('admin.mailCenter.actions.send') }}
        </LBtn>
        <LTag v-if="previewData" variant="info" size="sm">
          {{ $t('admin.mailCenter.recipients.resolved', { n: previewData.recipients.count }) }}
        </LTag>
      </div>
      </div>

      <!-- vertical resizer (LLARS standard) -->
      <div
        class="compose-resizer"
        role="separator"
        aria-orientation="vertical"
        @mousedown="startResize"
        @touchstart.prevent="startResize"
      >
        <div class="compose-resizer-grip"></div>
      </div>

      <!-- RIGHT: live preview -->
      <div class="compose-pane compose-preview-pane" :style="rightPanelStyle()">
        <LCard :title="$t('admin.mailCenter.preview.title')" icon="mdi-email-search-outline" class="preview-card">
          <div v-if="previewLoading" class="preview-state">
            <LLoading :text="$t('common.loading')" />
          </div>
          <template v-else-if="previewData">
            <div class="d-flex align-center justify-space-between mb-2" style="gap:8px;">
              <div class="text-truncate">
                <strong>{{ $t('admin.mailCenter.preview.subject') }}:</strong> {{ previewData.subject }}
              </div>
              <LBtn
                variant="text"
                size="small"
                prepend-icon="mdi-fullscreen"
                @click="openFullscreen(previewData.html, $t('admin.mailCenter.preview.title'), previewData.subject)"
              >
                {{ $t('admin.mailCenter.preview.fullscreen') }}
              </LBtn>
            </div>
            <iframe
              class="mail-preview-iframe mail-preview-iframe--full"
              :srcdoc="previewData.html"
              sandbox=""
              :title="previewData.subject"
            ></iframe>
            <div v-if="previewData.recipients.skipped_invalid || previewData.recipients.skipped_duplicate"
                 class="text-caption text-medium-emphasis mt-2">
              {{ $t('admin.mailCenter.preview.skipped', {
                invalid: previewData.recipients.skipped_invalid,
                dupes: previewData.recipients.skipped_duplicate,
              }) }}
            </div>
          </template>
          <div v-else class="preview-state preview-empty">
            <LIcon size="32">mdi-email-search-outline</LIcon>
            <p>{{ $t('admin.mailCenter.preview.empty') }}</p>
          </div>
        </LCard>
      </div>
    </div>

    <!-- ========================= VERLAUF / SENT LOG ========================= -->
    <div v-else>
      <LCard :title="$t('admin.mailCenter.log.title')" icon="mdi-history" class="mb-4">
        <template #actions>
          <LBtn variant="text" size="small" prepend-icon="mdi-refresh" @click="loadLog">
            {{ $t('admin.mailCenter.log.refresh') }}
          </LBtn>
        </template>

        <p class="text-caption text-medium-emphasis mb-3">
          {{ $t('admin.mailCenter.log.help') }}
        </p>

        <v-row dense class="mb-2">
          <v-col cols="12" sm="3">
            <v-select
              v-model="logFilters.type"
              :items="typeOptions"
              :label="$t('admin.mailCenter.log.filterType')"
              variant="outlined"
              density="compact"
              clearable
              hide-details
              @update:model-value="loadLog"
            />
          </v-col>
          <v-col cols="12" sm="3">
            <v-select
              v-model="logFilters.status"
              :items="statusOptions"
              :label="$t('admin.mailCenter.log.filterStatus')"
              variant="outlined"
              density="compact"
              clearable
              hide-details
              @update:model-value="loadLog"
            />
          </v-col>
          <v-col cols="12" sm="3">
            <v-text-field
              v-model="logFilters.dateFrom"
              :label="$t('admin.mailCenter.log.filterDateFrom')"
              type="date"
              variant="outlined"
              density="compact"
              clearable
              hide-details
              @update:model-value="loadLog"
            />
          </v-col>
          <v-col cols="12" sm="3">
            <v-text-field
              v-model="logFilters.recipient"
              :label="$t('admin.mailCenter.log.filterRecipient')"
              variant="outlined"
              density="compact"
              clearable
              hide-details
              prepend-inner-icon="mdi-magnify"
              @keyup.enter="loadLog"
            />
          </v-col>
        </v-row>

        <!-- Empty-state hint: log only contains mails sent after logging deployed -->
        <v-alert
          v-if="!loading && logEntries.length === 0"
          type="info"
          variant="tonal"
          density="comfortable"
          class="my-3"
          icon="mdi-information-outline"
        >
          {{ $t('admin.mailCenter.log.emptyHint') }}
        </v-alert>

        <v-data-table
          v-else
          :headers="logHeaders"
          :items="logEntries"
          :loading="loading"
          :items-per-page="25"
          class="elevation-0"
        >
          <template #item.mail_type="{ item }">
            <LTag :variant="typeVariant(item.mail_type)" size="sm">{{ typeLabel(item.mail_type) }}</LTag>
          </template>
          <template #item.status="{ item }">
            <LTag :variant="statusVariant(item.status)" size="sm">{{ statusLabel(item.status) }}</LTag>
          </template>
          <template #item.scenario_id="{ item }">
            <!-- Referral-link rows: the "Link N" reference is clickable and
                 opens the actual branded mail (rendered for that link) in the
                 fullscreen preview, so the admin can see what the recipient got. -->
            <a
              v-if="item.referral_link_id"
              class="bezug-link"
              role="button"
              tabindex="0"
              @click="openMailForLog(item)"
              @keydown.enter="openMailForLog(item)"
            >{{ contextLabel(item) }}</a>
            <span v-else class="text-caption">{{ contextLabel(item) }}</span>
          </template>
          <template #item.created_at="{ item }">
            <span class="text-caption">{{ formatDate(item.created_at) }}</span>
          </template>
          <template #item.opened_at="{ item }">
            <LTag v-if="item.opened_at" variant="success" size="sm">{{ formatDate(item.opened_at) }}</LTag>
            <span v-else class="text-caption text-medium-emphasis">{{ $t('admin.mailCenter.log.notOpened') }}</span>
          </template>
          <template #item.clicked_at="{ item }">
            <LTag v-if="item.clicked_at" variant="info" size="sm">{{ formatDate(item.clicked_at) }}</LTag>
            <span v-else class="text-caption text-medium-emphasis">{{ $t('admin.mailCenter.log.notClicked') }}</span>
          </template>
        </v-data-table>
        <p class="text-caption text-medium-emphasis mt-2">
          <LIcon size="14" class="mr-1">mdi-information-outline</LIcon>{{ $t('admin.mailCenter.log.trackingHint') }}
        </p>
      </LCard>
    </div>

    <!-- Send confirmation -->
    <v-dialog v-model="confirmSend" max-width="460">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-send-check</v-icon>
          {{ $t('admin.mailCenter.confirm.title') }}
        </v-card-title>
        <v-card-text>
          {{ $t('admin.mailCenter.confirm.text', { n: previewData ? previewData.recipients.count : '?' }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="confirmSend = false">{{ $t('admin.mailCenter.confirm.cancel') }}</LBtn>
          <LBtn variant="primary" :loading="loading" @click="doSend">{{ $t('admin.mailCenter.confirm.confirm') }}</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fullscreen mail preview: the branded mail rendered large in an
         isolated iframe (used from template cards + the compose preview). -->
    <v-dialog v-model="fullscreenOpen" fullscreen :scrim="false" transition="dialog-bottom-transition">
      <div class="fullscreen-preview">
        <div class="fullscreen-bar">
          <div class="fullscreen-title">
            <LIcon size="18">mdi-email-search-outline</LIcon>
            <strong>{{ fullscreenTitle }}</strong>
            <span v-if="fullscreenSubject" class="text-medium-emphasis ml-2 text-truncate">— {{ fullscreenSubject }}</span>
          </div>
          <LBtn variant="text" prepend-icon="mdi-close" @click="fullscreenOpen = false">
            {{ $t('common.close') }}
          </LBtn>
        </div>
        <iframe
          class="fullscreen-iframe"
          :srcdoc="fullscreenHtml"
          sandbox=""
          :title="fullscreenTitle"
        ></iframe>
      </div>
    </v-dialog>
  </div>
</template>


<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDebounceFn } from '@vueuse/core'
import { usePanelResize } from '@/composables/usePanelResize'
import { useMailCenter } from '@/composables/useMailCenter'
import { useReferralSystem } from '@/composables/useReferralSystem'
import { useSnackbar } from '@/composables/useSnackbar'

// Branded per-org recruitment invitations are NOT served by any backend
// endpoint, so they're bundled as raw HTML assets (Vite `?raw`) and shown as
// extra slides in the template gallery. Keep filenames in sync with
// src/assets/recruitment-templates/.
import fafHtml from '@/assets/recruitment-templates/kann-ki-beratung-faf.html?raw'
import kizHtml from '@/assets/recruitment-templates/kann-ki-beratung-kiz.html?raw'
import iebHtml from '@/assets/recruitment-templates/kann-ki-beratung-ieb.html?raw'
import bvkeHtml from '@/assets/recruitment-templates/kann-ki-beratung-bvke.html?raw'
import bkeHtml from '@/assets/recruitment-templates/kann-ki-beratung-bke.html?raw'
import digiSuchtHtml from '@/assets/recruitment-templates/kann-ki-beratung-digi-sucht.html?raw'

const { t, locale } = useI18n()
const mail = useMailCenter()
const referral = useReferralSystem()
const { showSuccess, showError } = useSnackbar()

const loading = computed(() => mail.loading.value)

// Three clear areas: standard templates, compose/send, sent log.
const tab = ref('templates')
const tabs = computed(() => [
  { value: 'templates', label: t('admin.mailCenter.tabs.templates') },
  { value: 'compose', label: t('admin.mailCenter.tabs.compose') },
  { value: 'log', label: t('admin.mailCenter.tabs.log') },
])

const mode = ref('invitation')
const form = ref({ referralLinkId: null, intro: '', subject: '', body: '' })
const recipients = ref({ listText: '', referralLinkId: null, scenarioId: null, roleName: null })

const previewData = ref(null)
const previewLoading = ref(false)
const confirmSend = ref(false)

// -------- Branded-template invitation editing --------
// When the picked referral link's slug matches a bundled branded template, the
// admin edits that template's raw HTML directly (no generic render). This ref
// Referral links for the dropdowns (flattened from all campaigns). Declared up
// here (before selectedBrandedTemplate + its immediate watcher) so the watcher
// firing at setup doesn't hit a temporal-dead-zone ReferenceError.
const allLinks = ref([])

// holds the editable body; it's pre-filled from the template and reset whenever
// the selected link changes (simple reset — see watcher below).
const invitationBodyHtml = ref('')

// The branded template (html/org/subject) for the currently selected referral
// link, or null when the link has no matching branded template (→ generic flow).
const selectedBrandedTemplate = computed(() => {
  const link = allLinks.value.find(l => l.id === form.value.referralLinkId)
  if (!link) return null
  const slug = link.slug || link.code
  // IJCAI-Demo-Link (/join/ijcai) → die englische IJCAI-Welcome-Mail aus dem
  // Backend (Template-Typ 'ijcai'), statt des generischen Invitation-Renderings.
  if (slug === 'ijcai') {
    const t = templates.value.find(x => x.type === 'ijcai')
    return t ? { html: t.html, org: 'IJCAI 2026', subject: t.subject } : null
  }
  // Allgemeine LLARS-Demo-Links (/join/demo-de, /join/demo-en) → die sprach-
  // spezifische Demo-Einladung aus dem Backend.
  if (slug === 'demo-de' || slug === 'demo-en') {
    const type = slug === 'demo-en' ? 'demo_invitation_en' : 'demo_invitation_de'
    const t = templates.value.find(x => x.type === type)
    return t ? { html: t.html, org: slug === 'demo-en' ? 'LLARS Demo (EN)' : 'LLARS Demo (DE)', subject: t.subject } : null
  }
  return (slug && RECRUITMENT_TEMPLATES_BY_SLUG[slug]) || null
})

// Fullscreen mail preview (template cards + compose preview).
const fullscreenOpen = ref(false)
const fullscreenHtml = ref('')
const fullscreenTitle = ref('')
const fullscreenSubject = ref('')
function openFullscreen(html, title, subject = '') {
  fullscreenHtml.value = html || ''
  fullscreenTitle.value = title || ''
  fullscreenSubject.value = subject || ''
  fullscreenOpen.value = true
}

// Open the branded invitation mail behind a log row's referral-link reference
// ("Link N") in the fullscreen preview. We render the current template for that
// link via the same preview endpoint the composer uses — the exact per-recipient
// body isn't persisted, but this faithfully shows the mail that link sends.
async function openMailForLog(item) {
  if (!item?.referral_link_id) return
  const ref = contextLabel(item)
  const who = item.recipient_email ? `${ref} → ${item.recipient_email}` : ref
  try {
    const data = await mail.preview({ mode: 'invitation', referral_link_id: item.referral_link_id })
    openFullscreen(data.html, who, data.subject || item.subject || '')
  } catch (e) {
    showError(e.message)
  }
}

// Side-by-side composer ↔ live-preview with the LLARS vertical resizer.
const { containerRef, startResize, leftPanelStyle, rightPanelStyle } = usePanelResize({
  initialLeftPercent: 46,
  minLeftPercent: 30,
  maxLeftPercent: 70,
  storageKey: 'mailcenter-compose-split',
})

// Pre-fill (and reset) the editable branded-template body whenever the selected
// referral link resolves to a branded template. Simple reset on change — if the
// admin had edits they're discarded, which is acceptable here (the source of
// truth is the branded template). Non-branded links clear the body so the
// generic flow takes over.
watch(
  selectedBrandedTemplate,
  (tpl) => { invitationBodyHtml.value = tpl ? tpl.html : '' },
  { immediate: true }
)

// Live preview: re-render (debounced) whenever the mail content changes, so the
// right pane always reflects the current draft without a manual button. For
// branded-template invitations the preview is driven client-side from the
// edited HTML (see doPreview), but we still resolve the recipient count.
const canPreview = computed(() =>
  mode.value === 'invitation'
    ? !!form.value.referralLinkId
    : !!(form.value.subject || form.value.body)
)
const autoPreview = useDebounceFn(() => {
  if (!canPreview.value) { previewData.value = null; return }
  doPreview()
}, 500)
watch(
  [
    mode,
    () => form.value.referralLinkId,
    () => form.value.intro,
    () => form.value.subject,
    () => form.value.body,
    () => recipients.value.listText,
    invitationBodyHtml,
  ],
  () => autoPreview()
)

const roleOptions = ['admin', 'researcher', 'evaluator', 'chatbot_manager']

// Referral links for the dropdowns (flattened from all campaigns).
// `allLinks` is declared earlier (near selectedBrandedTemplate) to avoid a TDZ.
const linkOptions = computed(() =>
  allLinks.value.map(l => ({ value: l.id, label: `${l.label || l.slug || l.code} (${l.slug || l.code})` }))
)

async function loadLinks() {
  try {
    const campaigns = await referral.listCampaigns(false)
    const links = []
    for (const c of campaigns) {
      const cl = await referral.listCampaignLinks(c.id)
      links.push(...cl)
    }
    allLinks.value = links
  } catch (e) {
    // Non-fatal: composer still works with the pasted list.
    showError(e.message)
  }
}

// -------- Standard templates (Vorlagen tab) --------
const templates = ref([])
const templatesLoading = ref(false)

async function loadTemplates() {
  templatesLoading.value = true
  try {
    templates.value = await mail.fetchTemplates()
    // Reset the gallery to the first slide once the new track has rendered.
    await nextTick()
    if (trackRef.value) trackRef.value.scrollLeft = 0
    activeSlide.value = 0
  } catch (e) {
    showError(e.message)
  } finally {
    templatesLoading.value = false
  }
}

// -------- Branded study recruitment invitations (bundled assets) --------
// Proper-noun org labels are hardcoded (they don't translate); the shared
// subject + the section header/note are i18n'd. Each carries `recruitment:true`
// so the slider can badge it as a study template.
const RECRUITMENT_SUBJECT = 'Einladung zur Studie „Kann KI Beratung?“'
const recruitmentSlides = [
  { key: 'faf', label: 'Einladung · Friends & Family', html: fafHtml },
  { key: 'kiz', label: 'Einladung · KI-Zentrum Bayern', html: kizHtml },
  { key: 'ieb', label: 'Einladung · Institut für E-Beratung', html: iebHtml },
  { key: 'bvke', label: 'Einladung · BVkE', html: bvkeHtml },
  { key: 'bke', label: 'Einladung · bke', html: bkeHtml },
  { key: 'digi-sucht', label: 'Einladung · DigiSucht', html: digiSuchtHtml },
].map(s => ({
  ...s,
  subject: RECRUITMENT_SUBJECT,
  icon: 'mdi-account-multiple-plus',
  variant: 'accent',
  recruitment: true,
}))

// Map a referral-link slug → its branded invitation template. The referral
// links carry slugs like `kann-ki-beratung-faf`, while the bundled templates
// are keyed by the bare org id (`faf`, `digi-sucht`, …). So the lookup key is
// `kann-ki-beratung-<key>`. `label.split('·')[1]` is the human org name used in
// the "Gebrandete Vorlage · <org>" badge. Used by the invitation composer to
// pre-fill an editable HTML body when a branded link is picked.
const RECRUITMENT_TEMPLATES_BY_SLUG = recruitmentSlides.reduce((acc, s) => {
  acc[`kann-ki-beratung-${s.key}`] = {
    html: s.html,
    // org portion of "Einladung · <Org>" → used in the editable badge.
    org: s.label.includes('·') ? s.label.split('·')[1].trim() : s.label,
    subject: s.subject,
  }
  return acc
}, {})

// Combined slider track: system templates first, then the branded study
// invitations. A single normalized shape keeps the template markup simple.
const slides = computed(() => [
  ...templates.value.map(tpl => ({
    key: `sys-${tpl.type}`,
    type: tpl.type,
    label: typeLabel(tpl.type),
    subject: tpl.subject,
    html: tpl.html,
    description: tpl.description,
    variables: tpl.variables,
    icon: typeIcon(tpl.type),
    variant: typeVariant(tpl.type),
    recruitment: false,
  })),
  ...recruitmentSlides,
])

// -------- Quick send: ship a chosen template to one entered address --------
// Each Vorlagen card has a "Schnellversand" button that toggles an inline email
// field for THAT card; sending dispatches the template to the entered address.
// System templates send by `type`; bundled study invitations (no type) send
// their raw HTML verbatim. Mirrors the Compose send UX but for a single card.
const quickSendKey = ref(null)
const quickSendEmail = ref('')
const quickSendLoading = ref(false)

function toggleQuickSend(slide) {
  if (quickSendKey.value === slide.key) {
    quickSendKey.value = null
  } else {
    quickSendKey.value = slide.key
    quickSendEmail.value = ''
  }
}

async function doQuickSend(slide) {
  const email = (quickSendEmail.value || '').trim()
  if (!email || quickSendLoading.value) return
  quickSendLoading.value = true
  try {
    const res = await mail.sendTemplate({
      type: slide.recruitment ? null : slide.type,
      subject: slide.subject,
      bodyHtml: slide.recruitment ? slide.html : null,
      email,
    })
    const r = res.result || {}
    const to = r.email || email
    if (r.status === 'sent') {
      showSuccess(t('admin.mailCenter.quickSend.sent', { email: to }))
    } else if (r.status === 'skipped') {
      showError(t('admin.mailCenter.quickSend.skipped', { email: to }))
    } else {
      showError(t('admin.mailCenter.quickSend.failed', { email: to }))
    }
    quickSendKey.value = null
    quickSendEmail.value = ''
    loadLog()
  } catch (e) {
    showError(e.message)
  } finally {
    quickSendLoading.value = false
  }
}

// -------- Slider navigation (arrows, dots, scroll-snap sync) --------
const trackRef = ref(null)
const activeSlide = ref(0)

// Width of one snap step = slide width + gap, derived from the first slide so
// arrow/dot navigation lands exactly on a snap point regardless of viewport.
function slideStep() {
  const track = trackRef.value
  if (!track || !track.firstElementChild) return 0
  const gap = parseFloat(getComputedStyle(track).columnGap || '0') || 0
  return track.firstElementChild.getBoundingClientRect().width + gap
}

// Keep the active dot in sync while the user free-scrolls/swipes the track.
function onTrackScroll() {
  const step = slideStep()
  if (!step) return
  activeSlide.value = Math.round(trackRef.value.scrollLeft / step)
}

function goToSlide(i) {
  const track = trackRef.value
  if (!track) return
  activeSlide.value = i
  track.scrollTo({ left: i * slideStep(), behavior: 'smooth' })
}

function scrollSlides(dir) {
  const next = Math.min(Math.max(activeSlide.value + dir, 0), slides.value.length - 1)
  goToSlide(next)
}

const canSend = computed(() => {
  if (mode.value === 'invitation') return !!form.value.referralLinkId
  return !!form.value.subject && !!form.value.body
})

function buildRecipientSpec() {
  return {
    list_text: recipients.value.listText,
    referral_link_id: recipients.value.referralLinkId || undefined,
    scenario_id: recipients.value.scenarioId || undefined,
    role_name: recipients.value.roleName || undefined,
  }
}

async function doPreview() {
  previewLoading.value = true
  try {
    if (mode.value === 'invitation') {
      // Branded template selected → preview the EDITED html verbatim. The
      // backend echoes body_html/subject back (and still resolves the recipient
      // count); for non-branded links it renders the generic invitation.
      const branded = selectedBrandedTemplate.value
      previewData.value = await mail.preview({
        mode: 'invitation',
        referral_link_id: form.value.referralLinkId,
        intro: form.value.intro,
        list_text: recipients.value.listText,
        ...(branded ? { body_html: invitationBodyHtml.value, subject: RECRUITMENT_SUBJECT } : {}),
      })
    } else {
      previewData.value = await mail.preview({
        mode: 'announcement',
        subject: form.value.subject,
        body: form.value.body,
        recipient_spec: buildRecipientSpec(),
      })
    }
  } catch (e) {
    showError(e.message)
  } finally {
    previewLoading.value = false
  }
}

async function doSend() {
  try {
    let res
    if (mode.value === 'invitation') {
      // Branded template → send the EDITED html verbatim with the proven
      // descriptive subject; otherwise fall back to the generic invitation.
      const branded = selectedBrandedTemplate.value
      res = await mail.sendInvite({
        referralLinkId: form.value.referralLinkId,
        listText: recipients.value.listText,
        intro: form.value.intro,
        ...(branded ? { bodyHtml: invitationBodyHtml.value, subject: RECRUITMENT_SUBJECT } : {}),
      })
    } else {
      res = await mail.sendAnnouncement({
        subject: form.value.subject,
        body: form.value.body,
        recipientSpec: buildRecipientSpec(),
      })
    }
    confirmSend.value = false
    const r = res.result || {}
    showSuccess(t('admin.mailCenter.messages.sent', { sent: r.sent || 0, failed: r.failed || 0, skipped: r.skipped || 0 }))
    previewData.value = null
    loadLog()
  } catch (e) {
    showError(e.message)
  }
}

// -------- Mail log --------
const logEntries = ref([])
const logFilters = ref({ type: null, status: null, recipient: '', dateFrom: null })
const logHeaders = computed(() => [
  { title: t('admin.mailCenter.log.headers.date'), key: 'created_at', sortable: true },
  { title: t('admin.mailCenter.log.headers.type'), key: 'mail_type', sortable: true },
  { title: t('admin.mailCenter.log.headers.recipient'), key: 'recipient_email', sortable: true },
  { title: t('admin.mailCenter.log.headers.subject'), key: 'subject', sortable: false },
  { title: t('admin.mailCenter.log.headers.context'), key: 'scenario_id', sortable: false },
  { title: t('admin.mailCenter.log.headers.status'), key: 'status', sortable: true },
  { title: t('admin.mailCenter.log.columns.opened'), key: 'opened_at', sortable: true },
  { title: t('admin.mailCenter.log.columns.clicked'), key: 'clicked_at', sortable: true },
])

const typeOptions = computed(() => ['welcome', 'password_reset', 'invitation', 'announcement']
  .map(v => ({ title: typeLabel(v), value: v })))
const statusOptions = computed(() => ['sent', 'failed', 'skipped']
  .map(v => ({ title: statusLabel(v), value: v })))

async function loadLog() {
  try {
    const params = {}
    if (logFilters.value.type) params.type = logFilters.value.type
    if (logFilters.value.status) params.status = logFilters.value.status
    if (logFilters.value.recipient) params.recipient = logFilters.value.recipient
    if (logFilters.value.dateFrom) params.date_from = logFilters.value.dateFrom
    const data = await mail.fetchLog(params)
    logEntries.value = data.entries
  } catch (e) {
    showError(e.message)
  }
}

function typeLabel(t0) { return t(`admin.mailCenter.types.${t0}`) }
function statusLabel(s) { return t(`admin.mailCenter.statuses.${s}`) }
function typeVariant(t0) {
  return { welcome: 'success', password_reset: 'warning', invitation: 'info', ijcai: 'accent', demo_invitation_de: 'accent', demo_invitation_en: 'accent', announcement: 'secondary' }[t0] || 'secondary'
}
function typeIcon(t0) {
  return {
    welcome: 'mdi-hand-wave',
    password_reset: 'mdi-lock-reset',
    invitation: 'mdi-account-multiple-plus',
    ijcai: 'mdi-presentation',
    demo_invitation_de: 'mdi-presentation-play',
    demo_invitation_en: 'mdi-presentation-play',
    announcement: 'mdi-bullhorn',
  }[t0] || 'mdi-email'
}
function statusVariant(s) {
  return { sent: 'success', failed: 'danger', skipped: 'warning' }[s] || 'secondary'
}
// Short scenario/link context for a log row, or a dash when none applies.
function contextLabel(item) {
  if (item.scenario_id) return t('admin.mailCenter.log.scenarioRef', { id: item.scenario_id })
  if (item.referral_link_id) return t('admin.mailCenter.log.linkRef', { id: item.referral_link_id })
  return '-'
}
function formatDate(iso) {
  if (!iso) return '-'
  const loc = locale.value === 'de' ? 'de-DE' : 'en-US'
  return new Date(iso).toLocaleString(loc, { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadTemplates()
  loadLinks()
  loadLog()
})
</script>

<style scoped>
/* The admin section wrapper (.section-container--full) is overflow:hidden and
   expects each section to manage its own scrolling. The compose tab self-scrolls
   (compose-split), but the templates + log tabs need the component itself to
   scroll — otherwise long mail-history lists get clipped with no way to reach
   the rest / the pagination footer. */
.admin-mail-center { padding: 0; height: 100%; overflow-y: auto; }
/* ===== Full-width sliding template gallery (iPad-landscape cover-flow) =====
   The track fills the available width and snaps one prominent slide at a time;
   the inset slide width (~88%) lets the neighbouring slides peek at the edges.
   Arrows sit centred over the track edges, the dot rail sits below. This
   replaces the old fixed-380px flex row that left big empty gutters. */
.template-slider {
  position: relative;
  width: 100%;
}
.slider-track {
  display: flex;
  gap: 24px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  /* Side padding = the peek of the neighbouring slide; bottom padding clears
     the scrollbar so it doesn't overlap the card. */
  padding: 6px 6%;
  scrollbar-width: thin;
}
.slider-track::-webkit-scrollbar { height: 8px; }
.slider-track::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.18);
  border-radius: 8px;
}
.slider-slide {
  flex: 0 0 88%;
  max-width: 88%;
  scroll-snap-align: center;
  /* Inactive neighbours recede slightly — the cover-flow focus cue. */
  transform: scale(0.97);
  opacity: 0.72;
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.slider-slide--active {
  transform: scale(1);
  opacity: 1;
}
.slide-card { height: 100%; }
.slide-iframe { height: 480px; }

/* Arrows: floating, asymmetric-radius pills over the track edges. */
.slider-arrow {
  position: absolute;
  top: 46%;
  z-index: 2;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 16px 4px 16px 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
}
.slider-arrow--prev { left: 8px; }
.slider-arrow--next { right: 8px; }

/* Dot / position rail. Recruitment dots get an accent tint so the study block
   is visible at a glance; the active dot is wider + primary-coloured. */
.slider-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 14px;
  flex-wrap: wrap;
}
.slider-dot {
  width: 9px;
  height: 9px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  cursor: pointer;
  background: rgba(var(--v-theme-on-surface), 0.22);
  transition: width 0.2s ease, background 0.2s ease;
}
.slider-dot--recruitment { background: rgba(var(--v-theme-accent), 0.4); }
.slider-dot--active {
  width: 22px;
  border-radius: 6px 2px 6px 2px;
  background: var(--llars-primary, #b0ca97);
}

/* Narrower admin viewport: give slides nearly the full width (smaller peek). */
@media (max-width: 1100px) {
  .slider-slide { flex-basis: 92%; max-width: 92%; }
  .slider-track { padding: 6px 4%; }
  .slide-iframe { height: 420px; }
}
@media (max-width: 700px) {
  .slider-slide { flex-basis: 96%; max-width: 96%; }
  .slider-track { padding: 4px 2%; gap: 14px; }
}

/* Clickable "Link N" reference in the mail log → opens the branded mail. */
.bezug-link {
  color: rgb(var(--v-theme-primary));
  cursor: pointer;
  font-size: 0.8rem;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.bezug-link:hover { opacity: 0.8; }
.mail-preview-frame {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: var(--llars-radius-sm, 8px);
  padding: 8px;
  max-height: 420px;
  overflow-y: auto;
  background: #f4f6f2;
}

/* Isolated mail preview (iframe) — renders the full branded mail faithfully. */
.mail-preview-iframe {
  width: 100%;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: var(--llars-radius-sm, 8px);
  background: #ffffff;
  display: block;
}

/* Inline per-card quick-send panel (Vorlagen → Schnellversand). */
.quick-send-panel {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  padding-top: 12px;
}

/* Fullscreen mail preview overlay. */
.fullscreen-preview {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: rgb(var(--v-theme-surface));
}
.fullscreen-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  background: rgba(var(--v-theme-surface-variant), 0.3);
}
.fullscreen-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  min-width: 0;
}
.fullscreen-iframe {
  flex: 1;
  width: 100%;
  border: 0;
  background: #ffffff;
}
/* Compose right pane: fill the available viewport height; pane scrolls if taller. */
.mail-preview-iframe--full {
  height: calc(100vh - 360px);
  min-height: 380px;
}

/* Raw-HTML branded-template editor: full-width monospace so the admin can read
   the markup. Targets the inner <textarea> rendered by Vuetify's v-textarea. */
.template-html-editor :deep(textarea) {
  font-family: var(--llars-font-mono, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace);
  font-size: 12px;
  line-height: 1.5;
  white-space: pre;
  overflow-wrap: normal;
}

/* ===== Compose: side-by-side form | live preview with vertical resizer ===== */
.compose-split {
  display: flex;
  align-items: stretch;
  /* Fit on one screen; each pane scrolls internally (AppBar + tab bar ≈ 240px). */
  height: calc(100vh - 240px);
  min-height: 460px;
}
.compose-pane {
  height: 100%;
  overflow-y: auto;
  min-width: 0;
}
.compose-form-pane { padding-right: 10px; }
.compose-preview-pane { padding-left: 10px; }
.compose-preview-pane .preview-card { height: 100%; }

.compose-resizer {
  flex: 0 0 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: col-resize;
  touch-action: none;
}
.compose-resizer-grip {
  width: 4px;
  height: 52px;
  border-radius: 4px;
  background: rgba(var(--v-theme-on-surface), 0.18);
  transition: background 0.15s ease;
}
.compose-resizer:hover .compose-resizer-grip,
.compose-resizer:active .compose-resizer-grip {
  background: var(--llars-primary, #b0ca97);
}

/* In the right pane the pane itself scrolls — let the preview grow naturally. */
.mail-preview-frame--full {
  max-height: none;
}

.preview-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 240px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Stack vertically on narrow screens (resizer hidden). */
@media (max-width: 900px) {
  .compose-split {
    flex-direction: column;
    height: auto;
  }
  .compose-pane {
    width: 100% !important;
    height: auto;
  }
  .compose-form-pane { padding-right: 0; }
  .compose-preview-pane { padding-left: 0; }
  .compose-resizer { display: none; }
}
</style>
