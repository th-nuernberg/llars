<template>
  <v-dialog
    :model-value="modelValue"
    max-width="420"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card class="l-qr-card">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-qrcode</v-icon>
        {{ $t('admin.referral.qr.title') }}
      </v-card-title>

      <v-card-text class="text-center">
        <!-- Rendered QR (canvas-based PNG source) -->
        <div class="qr-frame mx-auto mb-3">
          <canvas ref="canvasEl" class="qr-canvas" />
          <LLoading v-if="rendering" :text="$t('admin.referral.qr.rendering')" />
          <div v-else-if="renderError" class="text-error text-caption pa-4">
            {{ renderError }}
          </div>
        </div>

        <!-- The public join URL underneath the QR -->
        <code class="qr-url d-block text-caption text-primary mb-1">{{ url }}</code>

        <div class="d-flex justify-center flex-wrap" style="gap: 8px;">
          <LBtn
            variant="primary"
            size="small"
            prepend-icon="mdi-file-image"
            :disabled="rendering || !!renderError"
            @click="downloadPng"
          >
            {{ $t('admin.referral.qr.downloadPng') }}
          </LBtn>
          <LBtn
            variant="secondary"
            size="small"
            prepend-icon="mdi-svg"
            :disabled="rendering || !!renderError"
            @click="downloadSvg"
          >
            {{ $t('admin.referral.qr.downloadSvg') }}
          </LBtn>
          <LBtn
            variant="accent"
            size="small"
            prepend-icon="mdi-file-pdf-box"
            :disabled="rendering || !!renderError"
            @click="downloadPdf"
          >
            {{ $t('admin.referral.qr.downloadPdf') }}
          </LBtn>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <LBtn variant="cancel" @click="$emit('update:modelValue', false)">
          {{ $t('admin.referral.qr.close') }}
        </LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
/**
 * LQrCodeDialog - LLARS Global QR-Code Dialog
 *
 * Renders a QR code for an arbitrary URL inside a modal and offers PNG, SVG and
 * PDF downloads. Built for the admin referral-link UI but kept generic (URL +
 * filename base) so it can be reused anywhere a downloadable QR is needed.
 *
 * Generation strategy (all client-side, no backend round-trip):
 * - PNG: qrcode.toCanvas() draws into the on-screen <canvas>; canvas.toDataURL()
 *   yields the PNG that is downloaded. Re-using the visible canvas keeps the
 *   preview and the download byte-identical.
 * - SVG: qrcode.toString({ type: 'svg' }) returns vector markup downloaded as a
 *   Blob — crisp at any print size.
 * - PDF: the PNG data URL is embedded centered on a single A4 page via jsPDF.
 *
 * The component lazy-imports qrcode/jspdf inside the handlers so the (heavy)
 * libraries are only pulled into the bundle chunk when a QR is actually opened.
 */
import { ref, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import LBtn from '@/components/common/LBtn.vue'
import LLoading from '@/components/common/LLoading.vue'

const props = defineProps({
  /** v-model: dialog open state */
  modelValue: { type: Boolean, default: false },
  /** The URL to encode in the QR code */
  url: { type: String, required: true },
  /** Filename base (without extension), e.g. "llars-join-my-slug" */
  filenameBase: { type: String, default: 'qr-code' }
})

defineEmits(['update:modelValue'])

const { t } = useI18n()

const canvasEl = ref(null)
const rendering = ref(false)
const renderError = ref('')

// Pixel resolution of the rendered/downloaded PNG. 1024px keeps print quality
// high while staying small enough for an instant in-dialog preview.
const QR_SIZE = 1024

/**
 * Draw the QR into the on-screen canvas whenever the dialog opens or the URL
 * changes. The same canvas is later read for the PNG/PDF exports.
 */
async function renderCanvas() {
  if (!props.url) return
  rendering.value = true
  renderError.value = ''
  try {
    const QRCode = (await import('qrcode')).default
    // Wait for the <canvas> to exist in the DOM (dialog content is lazy-mounted).
    await nextTick()
    if (!canvasEl.value) return
    await QRCode.toCanvas(canvasEl.value, props.url, {
      width: QR_SIZE,
      margin: 2,
      errorCorrectionLevel: 'M'
    })
  } catch (e) {
    renderError.value = t('admin.referral.qr.renderFailed')
  } finally {
    rendering.value = false
  }
}

// Re-render on open and on URL changes.
watch(
  () => [props.modelValue, props.url],
  ([open]) => {
    if (open) renderCanvas()
  },
  { immediate: true }
)

/** Trigger a browser download for a Blob or object/data URL. */
function triggerDownload(href, filename) {
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
}

function downloadPng() {
  if (!canvasEl.value) return
  const dataUrl = canvasEl.value.toDataURL('image/png')
  triggerDownload(dataUrl, `${props.filenameBase}.png`)
}

async function downloadSvg() {
  try {
    const QRCode = (await import('qrcode')).default
    const svg = await QRCode.toString(props.url, {
      type: 'svg',
      margin: 2,
      errorCorrectionLevel: 'M'
    })
    const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
    const objectUrl = URL.createObjectURL(blob)
    triggerDownload(objectUrl, `${props.filenameBase}.svg`)
    // Revoke after the click has been processed.
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
  } catch (e) {
    renderError.value = t('admin.referral.qr.renderFailed')
  }
}

async function downloadPdf() {
  if (!canvasEl.value) return
  try {
    const { jsPDF } = await import('jspdf')
    const pngDataUrl = canvasEl.value.toDataURL('image/png')
    const doc = new jsPDF({ unit: 'mm', format: 'a4' })
    const pageWidth = doc.internal.pageSize.getWidth()
    // Square QR image, 120mm wide, horizontally centered, ~40mm from the top.
    const imgSize = 120
    const x = (pageWidth - imgSize) / 2
    const y = 40
    doc.addImage(pngDataUrl, 'PNG', x, y, imgSize, imgSize)
    // Print the URL centered under the QR for paper-to-screen reference.
    doc.setFontSize(11)
    doc.text(props.url, pageWidth / 2, y + imgSize + 12, { align: 'center', maxWidth: imgSize + 40 })
    doc.save(`${props.filenameBase}.pdf`)
  } catch (e) {
    renderError.value = t('admin.referral.qr.renderFailed')
  }
}
</script>

<style scoped>
.l-qr-card {
  /* LLARS signature asymmetric border-radius */
  border-radius: 16px 4px 16px 4px;
}

.qr-frame {
  position: relative;
  width: 240px;
  height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  border-radius: 12px 3px 12px 3px;
  padding: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.qr-canvas {
  width: 100%;
  height: 100%;
  /* Keep crisp scaled-down rendering of the high-res canvas */
  image-rendering: pixelated;
}

.qr-url {
  word-break: break-all;
}
</style>
