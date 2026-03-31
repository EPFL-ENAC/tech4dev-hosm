<template>
  <q-page class="annotation-page">
    <q-card class="main-frame">
      <q-card-section v-if="selectedImage" class="image-section">
        <div class="viewer-controls">
          <q-btn-group unelevated square>
            <q-btn
              color="primary"
              no-caps
              label="Draw"
              icon="edit"
              :outline="!isDrawingMode"
              @click="setDrawMode(true)"
            />
            <q-btn
              color="primary"
              no-caps
              label="Move"
              icon="open_with"
              :outline="isDrawingMode"
              @click="setDrawMode(false)"
            />
          </q-btn-group>
        </div>

        <div span class="text-caption text-grey-7 q-mt-sm q-mb-sm">
          {{
            isDrawingMode
              ? 'Click to create a new annotation. Double-click to put last point. Click and drag to navigate.'
              : 'Click to select. Click and drag to move.'
          }}
        </div>

        <div id="openseadragon-container" class="openseadragon-container">
          <q-inner-loading :showing="imageIsLoading">
            <q-spinner-hourglass size="50px" color="grey-5" />
          </q-inner-loading>
        </div>
      </q-card-section>

      <q-card-section v-else class="empty-state">
        <div class="text-h5 text-grey-6">No annotated image</div>
        <div class="text-body1 text-grey-6 q-mt-sm">
          Use the sidebar to add an image to annotate.
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
import type { Annotation } from '../models';

const annotationStore = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();
const $q = useQuasar();

let viewer: OpenSeadragon.Viewer | null = null;
let annotator: ReturnType<typeof createOSDAnnotator> | null = null;
const isDrawingMode = ref(true);
const imageIsLoading = ref(false);

const selectedImage = computed(() => {
  if (!annotationStore.selectedImageUrl) return null;
  return annotationStore.annotatedImages.find(
    (img) => img.imageUrl === annotationStore.selectedImageUrl,
  );
});

function initializeViewer() {
  if (!annotationStore.selectedImageUrl) return;

  imageIsLoading.value = true;

  void nextTick(() => {
    const container = document.getElementById('openseadragon-container');
    if (!container) return;
    console.log('Initializing OpenSeadragon for image:', annotationStore.selectedImageUrl);

    try {
      viewer = OpenSeadragon({
        element: container,
        // id: 'openseadragon-container',
        prefixUrl: 'https://cdn.jsdelivr.net/gh/Benomrans/openseadragon-icons@main/images/',
        tileSources: {
          type: 'image',
          url: annotationStore.selectedImageUrl!,
        },
        autoHideControls: false,
        gestureSettingsMouse: {
          clickToZoom: false,
        },
        crossOriginPolicy: 'Anonymous',
        showNavigator: true,
        navigatorPosition: 'BOTTOM_RIGHT',
        navigatorSizeRatio: 0.2,
        preload: true,
      });

      viewer.addHandler('open', () => {
        imageIsLoading.value = false;
      });

      annotator = createOSDAnnotator(viewer, {
        autoSave: true,
        drawingEnabled: isDrawingMode.value,
      });

      annotator.setDrawingTool('polygon');

      const existingAnnotations = annotationStore.getAnnotationsForImage(
        annotationStore.selectedImageUrl!,
      );
      if (existingAnnotations.length > 0) {
        annotator.setAnnotations(existingAnnotations);
      }

      annotator.on('createAnnotation', (annotation: unknown) => {
        console.log('Created annotation:', annotation);
        annotationStore.addAnnotation(annotationStore.selectedImageUrl!, annotation as Annotation);
      });

      annotator.on('updateAnnotation', (annotation: unknown, previous: unknown) => {
        console.log('Updated annotation:', annotation, 'Previous:', previous);
        annotationStore.updateAnnotation(
          annotationStore.selectedImageUrl!,
          annotation as Annotation,
        );
      });

      annotator.on('deleteAnnotation', (annotation: unknown) => {
        console.log('Deleted annotation:', annotation);
        annotationStore.deleteAnnotation(
          annotationStore.selectedImageUrl!,
          annotation as Annotation,
        );
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

function setDrawMode(draw: boolean) {
  isDrawingMode.value = draw;
  if (annotator) {
    annotator.setDrawingEnabled(isDrawingMode.value);
  }
}

watch(
  () => annotationStore.selectedImageUrl,
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
  if (annotationStore.selectedImageUrl) {
    initializeViewer();
  }

  void datasetStore.loadImageUrls();
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
  box-shadow: none;
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
  height: calc(100vh - 153px); // Adjust based on header and controls height
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
