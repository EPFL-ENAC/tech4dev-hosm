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
              label="Select / Move"
              icon="open_with"
              :outline="isDrawingMode"
              @click="setDrawMode(false)"
            />
          </q-btn-group>

          <div :class="{ disabled: !selectedAnnotationId }">
            <q-tooltip v-if="!selectedAnnotationId" class="text-body2">
              Select an annotation to enable
            </q-tooltip>

            <span class="text-grey q-ml-lg">Damage level</span>
            <q-btn-toggle
              v-model="damageLevel"
              color="white"
              toggle-color="primary"
              text-color="primary"
              unelevated
              square
              :options="damageLevelOptions"
              :disable="!selectedAnnotationId"
              class="damage-levels q-ml-md"
              @update:model-value="updateDamageLevel"
            />

            <q-btn
              color="primary"
              unelevated
              square
              no-caps
              label="Delete"
              icon="delete"
              outline
              :disable="!selectedAnnotationId"
              @click="deleteAnnotation()"
              class="q-ml-lg"
            />
          </div>
        </div>

        <div span class="viewer-caption text-caption text-grey-7 q-mt-sm q-mb-sm">
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
import { useAnnotationDataStore, DAMAGE_LEVELS, DAMAGE_COLORS } from 'stores/annotation-data';
import { useDatasetImagesStore } from 'stores/dataset-images';
import type { Annotation } from '../models';

const annotationStore = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();
const $q = useQuasar();

let viewer: OpenSeadragon.Viewer | null = null;
let annotator: ReturnType<typeof createOSDAnnotator> | null = null;
const isDrawingMode = ref(true);
const imageIsLoading = ref(false);
const selectedAnnotationId = ref<string | null>(null);

const damageLevelOptions = [...Array(DAMAGE_LEVELS).keys()].map((level) => ({
  label: level.toString(),
  value: level,
}));
const damageLevel = ref<number>(0);

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

      const navigatorStyle = (document.getElementsByClassName('navigator')[0] as HTMLElement).style;
      navigatorStyle.background = 'white';
      navigatorStyle.opacity = '1';
      navigatorStyle.border = '1px solid #ccc';

      viewer.addHandler('open', () => {
        imageIsLoading.value = false;
      });

      annotator = createOSDAnnotator(viewer, {
        autoSave: true,
        drawingEnabled: isDrawingMode.value,
      });

      annotator.setDrawingTool('polygon');

      // @ts-expect-error - Typing too complex
      annotator.setStyle(
        (annotation: Annotation, state?: { selected: boolean; hovered: boolean }) => {
          if (!state) return {};
          if (!annotation.bodies[0]) return {};

          const damageLevel = annotation.bodies[0].value as unknown as number;
          const color = DAMAGE_COLORS[damageLevel];
          const opacity = state.selected ? 0.2 : state.hovered ? 0.7 : 0.8;

          return {
            fill: color,
            fillOpacity: opacity,
            stroke: color,
            strokeOpacity: 1,
          };
        },
      );

      const existingAnnotations = annotationStore.getAnnotationsForImage(
        annotationStore.selectedImageUrl!,
      );
      if (existingAnnotations.length > 0) {
        annotator.setAnnotations(existingAnnotations);
      }

      annotator.on('createAnnotation', (annotation: unknown) => {
        console.log('Created annotation:', annotation);
        (annotation as Annotation).bodies.push({
          purpose: 'damage',
          value: damageLevel.value,
        });
        annotator!.setSelected((annotation as Annotation).id); // Trigger redraw
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
        if (selected.length === 0) {
          selectedAnnotationId.value = null;
        } else {
          const annotation = selected[0] as Annotation;
          selectedAnnotationId.value = annotation.id;
          damageLevel.value = annotation.bodies[0]!.value;
        }
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

function deleteAnnotation() {
  if (!selectedAnnotationId.value || !annotator) return;

  annotator.removeAnnotation(selectedAnnotationId.value);
  selectedAnnotationId.value = null;
}

function updateDamageLevel(newLevel: number) {
  if (!annotator || !selectedAnnotationId.value) return;

  const annotation = annotator.getAnnotationById(selectedAnnotationId.value) as Annotation;
  annotation.bodies[0]!.value = newLevel;
  annotator.setSelected(annotation.id); // Trigger redraw
  annotationStore.updateAnnotation(annotationStore.selectedImageUrl!, annotation);
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
}

.main-frame {
  height: 100%;
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

.damage-levels {
  outline: 1px solid $primary !important;
}

.viewer-caption {
  flex-shrink: 0;
}

.openseadragon-container {
  width: 100%;
  height: calc(
    100vh - 154px
  ); // OpenSeadragon needs a height. Adjust based on header and controls height
  overflow: hidden;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
