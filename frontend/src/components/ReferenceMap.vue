<template>
  <div>
    <div class="viewer-controls q-mb-md">
      <q-btn-dropdown
        color="grey-8"
        unelevated
        square
        no-caps
        :label="currentSource"
        icon="layers"
        outline
      >
        <q-list>
          <q-item clickable v-close-popup @click="setSource('Esri')">
            <q-item-section>{{ t('esri') }}</q-item-section>
          </q-item>
          <q-item clickable v-close-popup @click="setSource('Bing')">
            <q-item-section>{{ t('bing') }}</q-item-section>
          </q-item>
          <q-item clickable v-close-popup @click="setSource('MapBox')">
            <q-item-section>{{ t('mapbox') }}</q-item-section>
          </q-item>
        </q-list>
      </q-btn-dropdown>

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

const DEFAULT_CENTER: [number, number] = [27.7172, 85.324]; // Kathmandu, Nepal
const DEFAULT_ZOOM_LEVEL = 18;
const SOURCES = ['Esri', 'Bing', 'MapBox'];
const TILE_SIZE = 512;
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

function setEsriSource() {
  return [
    {
      url: 'https://services.arcgisonline.com/ArcGis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      tileSize: TILE_SIZE,
    },
  ];
}

function setBingSource() {
  return setEsriSource();
}

function setMapBoxSource() {
  return setEsriSource();
}

function setSource(source: string) {
  currentSource.value = source;
  localStorage.setItem('mapTileSource', source);

  const sourceFunctions: Record<string, () => { url: string; tileSize: number }[]> = {
    Esri: setEsriSource,
    Bing: setBingSource,
    MapBox: setMapBoxSource,
  };

  const fn = sourceFunctions[source];
  if (fn) {
    const tilesConfig = fn();
    updateMapTiles(tilesConfig);
  }
}

function updateMapTiles(tilesConfig: { url: string; tileSize: number }[]) {
  if (!map) return;

  const style = map.getStyle();
  if (style && style.sources && style.sources.satellite) {
    const source = style.sources.satellite as { tiles?: string[]; tileSize?: number };
    source.tiles = tilesConfig.map((c) => c.url);
    if (tilesConfig.length > 0) {
      source.tileSize = tilesConfig[0]!.tileSize;
    }
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

onMounted(() => {
  const savedSource = localStorage.getItem('mapTileSource');
  if (savedSource && SOURCES.includes(savedSource)) {
    currentSource.value = savedSource;
  }

  const sourceFunctions: Record<string, () => { url: string; tileSize: number }[]> = {
    Esri: setEsriSource,
    Bing: setBingSource,
    MapBox: setMapBoxSource,
  };

  const fn = sourceFunctions[currentSource.value];
  const tilesConfig = fn ? fn() : setEsriSource();

  map = new maplibregl.Map({
    container: mapContainer.value!,
    style: {
      version: 8,
      sources: {
        satellite: {
          type: 'raster',
          tiles: tilesConfig.map((c) => c.url),
          tileSize: tilesConfig[0]!.tileSize,
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

watch(currentSource, (newSource) => {
  const sourceFunctions: Record<string, () => { url: string; tileSize: number }[]> = {
    Esri: setEsriSource,
    Bing: setBingSource,
    MapBox: setMapBoxSource,
  };
  const fn = sourceFunctions[newSource];
  if (fn) {
    const tilesConfig = fn();
    updateMapTiles(tilesConfig);
  }
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
