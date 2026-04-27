<template>
  <div>
    <div class="viewer-controls q-mb-md">
      <q-select
        v-model="currentSource"
        :options="sourceOptions"
        emit-value
        map-options
        color="grey-8"
        unelevated
        square
        outlined
        no-caps
        dense
        icon="layers"
        @update:model-value="setSource"
      />

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
import { baseUrl } from 'boot/api';

interface TileSourceConfig {
  tiles: string[];
  tileSize: number;
  attribution?: string;
}

const DEFAULT_CENTER: [number, number] = [27.7172, 85.324]; // Kathmandu, Nepal
const DEFAULT_ZOOM_LEVEL = 17;
const TILE_SIZE = 256;
const LOCAL_STORAGE_KEY = 'mapTileSource';
const SOURCES = ['esri', 'azure', 'mapbox'] as const;
const sourceOptions = [
  { value: 'esri', label: 'Esri' },
  { value: 'azure', label: 'Azure' },
  { value: 'mapbox', label: 'MapBox' },
];
const currentSource = ref<string>('esri');

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

function getEsriConfig(): TileSourceConfig {
  return {
    tiles: [
      'https://services.arcgisonline.com/ArcGis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: TILE_SIZE,
  };
}

async function fetchTileConfig(
  endpoint: string,
  fallback: TileSourceConfig,
): Promise<TileSourceConfig> {
  try {
    const response = await fetch(`${baseUrl}/map/${endpoint}/tiles`);
    if (response.status === 501) {
      console.warn(`${endpoint.toUpperCase()}_KEY not configured on backend, falling back to Esri`);
      return fallback;
    }
    if (!response.ok) {
      console.error(`Failed to fetch ${endpoint} tile metadata:`, response.status);
      return fallback;
    }
    const data = await response.json();
    return {
      tiles: [data.tiles[0] ?? data.tiles[data.tiles.length - 1]],
      tileSize: data.tile_size,
      attribution: data.attribution,
    };
  } catch (error) {
    console.error(`${endpoint} tile fetch error:`, error);
    return fallback;
  }
}

async function loadAllSources(): Promise<Record<string, TileSourceConfig>> {
  const esri = getEsriConfig();
  const [azure, mapbox] = await Promise.all([
    fetchTileConfig('azure', esri),
    fetchTileConfig('mapbox', esri),
  ]);
  return { esri, azure, mapbox };
}

function setSource(source: string) {
  currentSource.value = source;
  localStorage.setItem(LOCAL_STORAGE_KEY, source);

  if (!map) return;

  SOURCES.forEach((s) => {
    const visible = s === source ? 'visible' : 'none';
    map!.setLayoutProperty(`${s}-layer`, 'visibility', visible);
  });
}

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

onMounted(async () => {
  const savedSource = localStorage.getItem(LOCAL_STORAGE_KEY);
  if (savedSource && SOURCES.includes(savedSource as (typeof SOURCES)[number])) {
    currentSource.value = savedSource;
  }

  const sources = await loadAllSources();

  const style: maplibregl.StyleSpecification = {
    version: 8,
    sources: {},
    layers: [],
  };

  for (const [id, config] of Object.entries(sources)) {
    (style.sources as Record<string, maplibregl.RasterSourceSpecification>)[id] = {
      type: 'raster',
      tiles: config.tiles,
      tileSize: config.tileSize,
      attribution: config.attribution || '',
    };
    style.layers.push({
      id: `${id}-layer`,
      type: 'raster',
      source: id,
      layout: {
        visibility: id === currentSource.value ? 'visible' : 'none',
      },
    });
  }

  map = new maplibregl.Map({
    container: mapContainer.value!,
    style,
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
