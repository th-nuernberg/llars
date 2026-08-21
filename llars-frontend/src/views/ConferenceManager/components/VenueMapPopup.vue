<template>
  <v-dialog v-model="dialogVisible" max-width="480">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon start size="20">mdi-map-marker-outline</v-icon>
        {{ city }}{{ country ? `, ${country}` : '' }}
        <v-spacer />
        <v-btn icon variant="text" size="small" @click="dialogVisible = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="pa-0">
        <!-- Loading -->
        <div v-if="loading" class="map-loading">
          <v-progress-circular indeterminate color="primary" size="28" />
          <span class="ml-2 text-caption">{{ t('conferenceManager.venueMap.geocoding') }}</span>
        </div>

        <!-- Error -->
        <div v-else-if="errorMsg" class="map-error">
          <v-icon color="warning" class="mr-1">mdi-alert-outline</v-icon>
          <span class="text-caption">{{ errorMsg }}</span>
        </div>

        <!-- Map -->
        <div ref="mapContainer" class="map-container" />

        <!-- Distance -->
        <div v-if="distance" class="distance-bar">
          <v-icon size="14" class="mr-1">mdi-airplane</v-icon>
          {{ distance }} {{ t('conferenceManager.venueMap.distance') }}
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import 'leaflet/dist/leaflet.css'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  city: { type: String, default: '' },
  country: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const mapContainer = ref(null)
const loading = ref(false)
const errorMsg = ref(null)
const distance = ref(null)

let mapInstance = null

const NUREMBERG = [49.4521, 11.0767]

watch(dialogVisible, async (open) => {
  if (open) {
    loading.value = true
    errorMsg.value = null
    distance.value = null
    await nextTick()
    await initMap()
  } else {
    destroyMap()
  }
})

onBeforeUnmount(() => destroyMap())

function destroyMap() {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
}

async function initMap() {
  try {
    const L = await import('leaflet')

    // Geocode venue
    const query = [props.city, props.country].filter(Boolean).join(', ')
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`,
      { headers: { 'Accept-Language': 'en' } }
    )
    const results = await res.json()

    if (!results.length) {
      errorMsg.value = t('conferenceManager.venueMap.geocodeFailed')
      loading.value = false
      return
    }

    const venueLat = parseFloat(results[0].lat)
    const venueLng = parseFloat(results[0].lon)
    const venueCoords = [venueLat, venueLng]

    loading.value = false
    await nextTick()

    destroyMap()

    mapInstance = L.map(mapContainer.value, {
      zoomControl: true,
      attributionControl: false,
    })

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
    }).addTo(mapInstance)

    // Nuremberg marker (green)
    const nrnIcon = L.divIcon({
      className: '',
      html: '<div style="width:12px;height:12px;border-radius:50%;background:#b0ca97;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3)"></div>',
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    })
    L.marker(NUREMBERG, { icon: nrnIcon })
      .addTo(mapInstance)
      .bindTooltip('Nuremberg', { permanent: false })

    // Venue marker (red-orange)
    const venueIcon = L.divIcon({
      className: '',
      html: '<div style="width:12px;height:12px;border-radius:50%;background:#c4735a;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3)"></div>',
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    })
    L.marker(venueCoords, { icon: venueIcon })
      .addTo(mapInstance)
      .bindTooltip(query, { permanent: false })

    // Great circle arc
    const arcPoints = interpolateArc(NUREMBERG, venueCoords, 50)
    L.polyline(arcPoints, {
      color: '#88c4c8',
      weight: 2,
      dashArray: '6, 4',
      opacity: 0.8,
    }).addTo(mapInstance)

    // Fit bounds + force resize after dialog layout settles
    const bounds = L.latLngBounds([NUREMBERG, venueCoords])
    mapInstance.fitBounds(bounds, { padding: [30, 30] })
    setTimeout(() => {
      if (mapInstance) {
        mapInstance.invalidateSize()
        mapInstance.fitBounds(bounds, { padding: [30, 30] })
      }
    }, 200)

    // Calculate haversine distance
    const km = haversineKm(NUREMBERG[0], NUREMBERG[1], venueLat, venueLng)
    distance.value = `${Math.round(km).toLocaleString()} km`
  } catch (err) {
    console.error('Map init error:', err)
    errorMsg.value = t('conferenceManager.venueMap.error')
    loading.value = false
  }
}

function interpolateArc(start, end, numPoints) {
  const toRad = (d) => (d * Math.PI) / 180
  const toDeg = (r) => (r * 180) / Math.PI

  const lat1 = toRad(start[0]), lng1 = toRad(start[1])
  const lat2 = toRad(end[0]), lng2 = toRad(end[1])

  const d = 2 * Math.asin(Math.sqrt(
    Math.sin((lat2 - lat1) / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin((lng2 - lng1) / 2) ** 2
  ))

  const points = []
  for (let i = 0; i <= numPoints; i++) {
    const f = i / numPoints
    const A = Math.sin((1 - f) * d) / Math.sin(d)
    const B = Math.sin(f * d) / Math.sin(d)
    const x = A * Math.cos(lat1) * Math.cos(lng1) + B * Math.cos(lat2) * Math.cos(lng2)
    const y = A * Math.cos(lat1) * Math.sin(lng1) + B * Math.cos(lat2) * Math.sin(lng2)
    const z = A * Math.sin(lat1) + B * Math.sin(lat2)
    points.push([toDeg(Math.atan2(z, Math.sqrt(x * x + y * y))), toDeg(Math.atan2(y, x))])
  }
  return points
}

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371
  const toRad = (d) => (d * Math.PI) / 180
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}
</script>

<style scoped>
.map-container {
  height: 300px;
  width: 100%;
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.map-loading,
.map-error {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.distance-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  font-size: 0.82rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}
</style>
