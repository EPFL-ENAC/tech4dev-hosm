<template>
  <q-page class="annotation-page">
    <q-card class="main-frame">
      <q-card-section v-if="selectedImage" class="image-section">
        <div class="viewer-controls q-mb-md">
          <q-btn
            ref="toggleBtn"
            color="primary"
            :label="isDrawingMode ? 'Move' : 'Draw'"
            icon="swap_horiz"
            @click="toggleDrawMode"
          />
          <span class="text-caption text-grey-7 q-ml-md">
            {{
              isDrawingMode ? 'Click and drag to create annotations' : 'Click and drag to navigate'
            }}
          </span>
        </div>

        <div id="openseadragon-container" class="openseadragon-container"></div>
      </q-card-section>

      <q-card-section v-else class="empty-state">
        <div class="text-h5 text-grey-6">No annotated image</div>
        <div class="text-body1 text-grey-6 q-mt-sm">
          Use the sidebar to select an image or annotate a new one
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted, nextTick, computed, onMounted } from 'vue';
import { useQuasar } from 'quasar';
import OpenSeadragon from 'openseadragon';
import { createOSDAnnotator } from '@annotorious/openseadragon';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { useDatasetImagesStore } from 'stores/dataset-images';
import type { W3CAnnotation } from '../models';

const store = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();
const $q = useQuasar();

let viewer: OpenSeadragon.Viewer | null = null;
let annotator: ReturnType<typeof createOSDAnnotator> | null = null;
const isDrawingMode = ref(true);
const toggleBtn = ref<HTMLElement | null>(null);

const selectedImage = computed(() => {
  if (!store.selectedImageUrl) return null;
  return store.annotatedImages.find((img) => img.imageUrl === store.selectedImageUrl);
});

function initializeViewer() {
  if (!store.selectedImageUrl) return;

  void nextTick(() => {
    const container = document.getElementById('openseadragon-container');
    if (!container) return;
    console.log('Initializing OpenSeadragon for image:', store.selectedImageUrl);

    try {
      viewer = OpenSeadragon({
        element: container,
        // id: 'openseadragon-container',
        // prefixUrl: 'https://cdn.jsdelivr.net/npm/openseadragon@6/build/openseadragon/images/',
        prefixUrl: 'https://cdn.jsdelivr.net/gh/Benomrans/openseadragon-icons@main/images/',
        tileSources: {
          type: 'image',
          url: store.selectedImageUrl!,
        },
        // gestureSettingsMouse: {
        //   clickToZoom: false,
        // },
        // drawer: "canvas",
        crossOriginPolicy: 'Anonymous',
        // showNavigator: true,
        // navigatorPosition: 'BOTTOM_RIGHT',
        // navigatorSizeRatio: 0.2,
      });

      annotator = createOSDAnnotator(viewer, {
        // autoSave: false,
        drawingEnabled: isDrawingMode.value,
        // multiSelect: true,
      });

      annotator.setDrawingTool('polygon');

      const existingAnnotations = store.getW3CAnnotationsForImage(store.selectedImageUrl!);
      if (existingAnnotations.length > 0) {
        annotator.setAnnotations(existingAnnotations);
      }

      annotator.on('createAnnotation', (annotation: unknown) => {
        store.addW3CAnnotation(store.selectedImageUrl!, annotation as W3CAnnotation);
      });

      annotator.on('updateAnnotation', (annotation: unknown) => {
        store.updateW3CAnnotation(store.selectedImageUrl!, annotation as W3CAnnotation);
      });

      annotator.on('deleteAnnotation', (annotation: unknown) => {
        store.deleteW3CAnnotation(store.selectedImageUrl!, annotation as W3CAnnotation);
      });

      annotator.on('selectionChanged', (selected: unknown[]) => {
        console.log('Selected annotations:', selected);
      });
    } catch (error) {
      console.error('Error initializing OpenSeadragon:', error);
      $q.dialog({
        title: 'Error Loading Image',
        message: 'Failed to load the image. Please try selecting a different image.',
        color: 'negative',
        persistent: true,
        ok: true,
      });
    }
  });
}

function destroyViewer() {
  if (annotator) {
    annotator.destroy();
    annotator = null;
  }
  if (viewer) {
    viewer.destroy();
    viewer = null;
  }
}

function toggleDrawMode() {
  isDrawingMode.value = !isDrawingMode.value;
  if (annotator) {
    annotator.setDrawingEnabled(isDrawingMode.value);
  }
  if (toggleBtn.value) {
    toggleBtn.value.innerHTML = isDrawingMode.value ? 'Move' : 'Draw';
  }
}

watch(
  () => store.selectedImageUrl,
  (newUrl, oldUrl) => {
    if (newUrl && newUrl !== oldUrl) {
      destroyViewer();
      initializeViewer();
    }
  },
);

onUnmounted(() => {
  destroyViewer();
});

onMounted(() => {
  void datasetStore.loadImageUrls();
  if (store.selectedImageUrl) {
    initializeViewer();
  }
});
</script>

<style scoped lang="scss">
.annotation-page {
  height: 100%;
  overflow: hidden;
}

.main-frame {
  height: 100%;
  overflow: hidden;
}

.image-section {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.viewer-controls {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.openseadragon-container {
  // flex: 1;
  width: 100%;
  height: calc(100vh - 100px); // Adjust based on header and controls height
  overflow: hidden;
  // border-radius: 4px;
  // background: #f5f5f5;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
