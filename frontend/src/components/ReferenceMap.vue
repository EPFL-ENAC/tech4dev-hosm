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
import { onMounted, ref, watch, type Ref, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { useDatasetImagesStore } from 'stores/dataset-images';
import { type ImageGPSLocation } from 'src/models';
import { baseUrl } from 'boot/api';

interface TileSourceConfig {
  url: string;
  tileSize: number;
  attribution?: string;
}

const DEFAULT_CENTER: [number, number] = [27.7172, 85.324]; // Kathmandu, Nepal
const DEFAULT_ZOOM_LEVEL = 17;
const SOURCES = ['Esri', 'Azure', 'MapBox'];
const sourceOptions = SOURCES.map((s) => ({ value: s, label: s }));
const TILE_SIZE = 256;
const LOCAL_STORAGE_KEY = 'mapTileSource';
const currentSource = ref<string>('Esri');

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

function setEsriSource(): Promise<TileSourceConfig[]> {
  return Promise.resolve([
    {
      url: 'https://services.arcgisonline.com/ArcGis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      tileSize: TILE_SIZE,
    },
  ]);
}

async function setAzureSource(): Promise<TileSourceConfig[]> {
  try {
    const response = await fetch(`${baseUrl}/map/azure/tiles`);
    if (response.status === 501) {
      console.warn('AZURE_MAPS_KEY not configured on backend, falling back to Esri');
      return setEsriSource();
    }
    if (!response.ok) {
      console.error('Failed to fetch Azure tile metadata:', response.status);
      return setEsriSource();
    }
    const data = await response.json();
    return [
      {
        url: data.tiles[0] ?? data.tiles[data.tiles.length - 1],
        tileSize: data.tile_size,
        attribution: data.attribution,
      },
    ];
  } catch (error) {
    console.error('Azure Maps tile fetch error:', error);
    return setEsriSource();
  }
}

function setMapBoxSource(): Promise<TileSourceConfig[]> {
  return setEsriSource();
}

async function setSource(source: string) {
  currentSource.value = source;
  localStorage.setItem(LOCAL_STORAGE_KEY, source);

  const sourceFunctions: Record<string, () => Promise<TileSourceConfig[]>> = {
    Esri: setEsriSource,
    Azure: setAzureSource,
    MapBox: setMapBoxSource,
  };

  const fn = sourceFunctions[source];
  if (fn) {
    const tilesConfig = await fn();
    updateMapTiles(tilesConfig);
  }
}

function updateMapTiles(tilesConfig: TileSourceConfig[]) {
  if (!map) return;

  const style = map.getStyle();
  if (style && style.sources && style.sources.satellite) {
    const source = style.sources.satellite as {
      tiles?: string[];
      tileSize?: number;
      attribution?: string;
    };
    source.tiles = tilesConfig.map((c) => c.url);
    source.tileSize = tilesConfig[0]!.tileSize;
    source.attribution = tilesConfig[0]?.attribution || '';
    void nextTick(() => {
      map?.triggerRepaint();
    });
  }
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
  if (savedSource && SOURCES.includes(savedSource)) {
    currentSource.value = savedSource;
  }

  const sourceFunctions: Record<string, () => Promise<TileSourceConfig[]>> = {
    Esri: setEsriSource,
    Azure: setAzureSource,
    MapBox: setMapBoxSource,
  };

  const fn = sourceFunctions[currentSource.value];
  const tilesConfig: TileSourceConfig[] = fn ? await fn() : await setEsriSource();

  map = new maplibregl.Map({
    container: mapContainer.value!,
    style: {
      version: 8,
      sources: {
        satellite: {
          type: 'raster',
          tiles: tilesConfig.map((c) => c.url),
          tileSize: tilesConfig[0]!.tileSize,
          attribution: tilesConfig[0]?.attribution || '',
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
