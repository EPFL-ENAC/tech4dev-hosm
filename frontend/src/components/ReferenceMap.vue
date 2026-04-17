<template>
  <div>
    <div class="viewer-controls q-mb-md">
      <q-btn
        color="grey-8"
        unelevated
        square
        no-caps
        :label="t('recenter')"
        icon="my_location"
        outline
        @click="recenterMap"
      />

      <q-btn
        color="grey-8"
        unelevated
        square
        no-caps
        :label="t('hideReferenceMap')"
        icon="map"
        outline
        v-if="referenceMapShown"
        @click="$emit('hideReferenceMap')"
      />
    </div>

    <div ref="mapContainer" class="maplibre-container"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, type Ref } from 'vue';
import { useI18n } from 'vue-i18n';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { useDatasetImagesStore } from 'stores/dataset-images';
import { type ImageGPSLocation } from 'src/models';

const DEFAULT_CENTER: [number, number] = [27.7172, 85.324]; // Kathmandu, Nepal
const DEFAULT_ZOOM_LEVEL = 18;

defineProps<{
  referenceMapShown: boolean;
}>();

defineEmits<{
  (e: 'hideReferenceMap'): void;
}>();

const { t } = useI18n();
const annotationStore = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();
const mapContainer = ref(null);
let map: maplibregl.Map | null = null;
const imageLocation: Ref<ImageGPSLocation | null> = ref(null);

function recenterMap() {
  if (!map || !imageLocation.value) return;
  map.easeTo({
    center: [imageLocation.value.longitude, imageLocation.value.latitude],
    zoom: DEFAULT_ZOOM_LEVEL,
  });
}

watch(
  () => annotationStore.selectedImageUrl,
  async (url) => {
    if (url) {
      imageLocation.value = await datasetStore.getImageLocation(url);
      recenterMap();
    }
  },
  { immediate: true },
);

onMounted(() => {
  map = new maplibregl.Map({
    container: mapContainer.value!,
    // style: "https://api.maptiler.com/maps/satellite-v4/style.json?key=...",
    style: {
      version: 8,
      sources: {
        satellite: {
          type: 'raster',
          tiles: [
            'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg',
          ],
          tileSize: 512,
        },
      },
      layers: [
        {
          id: 'satellite',
          type: 'raster',
          source: 'satellite',
        },
      ],
    },
    center: imageLocation.value
      ? [imageLocation.value.longitude, imageLocation.value.latitude]
      : DEFAULT_CENTER,
    zoom: 12,
  });

  map.addControl(new maplibregl.NavigationControl(), 'top-right');
  map.dragPan.enable();
  map.scrollZoom.enable();
  map.dragRotate.enable();
  map.touchZoomRotate.enable();
});
</script>

<style scoped lang="scss">
.viewer-controls {
  display: flex;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: flex-end;
}

.maplibre-container {
  width: 100%;
  height: calc(100vh - 134px);
  overflow: hidden;
}
</style>
