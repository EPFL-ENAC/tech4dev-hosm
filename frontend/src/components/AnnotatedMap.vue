<template>
  <div>
    <div class="viewer-controls">
      <q-btn-group unelevated class="q-mr-md">
        <q-btn
          color="primary"
          no-caps
          no-wrap
          :label="t('draw')"
          icon="edit"
          :outline="!isDrawingMode"
          @click="setDrawMode(true)"
        />
        <q-btn
          color="primary"
          no-caps
          no-wrap
          :label="t('selectMove')"
          icon="open_with"
          :outline="isDrawingMode"
          @click="setDrawMode(false)"
        />
      </q-btn-group>

      <div :class="{ disabled: !selectedAnnotationId }">
        <q-tooltip v-if="!selectedAnnotationId" class="text-body2">
          {{ t('selectAnnotationToEnable') }}
        </q-tooltip>

        <span class="text-grey q-mr-sm">{{ t('damageLevel') }}</span>
        <q-btn-toggle
          v-model="damageLevel"
          clearable
          color="white"
          toggle-color="primary"
          text-color="primary"
          unelevated
          dense
          no-caps
          :options="damageLevelOptions"
          :disable="!selectedAnnotationId"
          class="q-mr-lg damage-levels"
          @update:model-value="updateDamageLevel"
        >
          <template v-for="(opt, index) in damageLevelOptions" :key="opt.value" #[opt.slot]>
            <q-icon
              name="circle"
              size="1em"
              class="q-ml-xs"
              :style="{ color: DAMAGE_COLORS[index + 1] }"
            />
          </template>
        </q-btn-toggle>

        <q-btn
          color="primary"
          unelevated
          no-caps
          :label="t('delete')"
          icon="delete"
          outline
          :disable="!selectedAnnotationId"
          class="q-mr-md"
          @click="deleteAnnotation()"
        />
      </div>

      <q-btn
        color="grey-8"
        unelevated
        no-caps
        :label="t('showReferenceMap')"
        icon="map"
        outline
        v-if="!referenceMapShown"
        @click="$emit('showReferenceMap')"
      />
    </div>

    <div span class="viewer-caption text-caption text-grey-7 q-mt-sm q-mb-sm">
      {{ isDrawingMode ? t('captionDrawMode') : t('captionSelectMoveMode') }}
    </div>

    <div id="openseadragon-container" class="openseadragon-container">
      <q-inner-loading :showing="allLoading">
        <q-spinner-hourglass size="50px" color="grey-5" />
      </q-inner-loading>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted, nextTick, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useQuasar, Notify } from 'quasar';
import OpenSeadragon from 'openseadragon';
import { createOSDAnnotator } from '@annotorious/openseadragon';
import { useAnnotationDataStore, DAMAGE_LEVELS, DAMAGE_COLORS } from 'stores/annotation-data';
import type { Annotation } from '../models';

defineProps<{
  referenceMapShown: boolean;
}>();

defineEmits<{
  (e: 'showReferenceMap'): void;
}>();

const { t } = useI18n();
const annotationStore = useAnnotationDataStore();
const $q = useQuasar();

let viewer: OpenSeadragon.Viewer | null = null;
let annotator: ReturnType<typeof createOSDAnnotator> | null = null;
const isDrawingMode = ref(true);
const imageLoading = ref(false);
const annotatorLoading = ref(false);
const selectedAnnotationId = ref<string | null>(null);

const damageLevelOptions = computed(() =>
  [...Array(DAMAGE_LEVELS.length - 1).keys()].map((level) => ({
    label: t(`damageLevel_${DAMAGE_LEVELS[level + 1]}`),
    value: level + 1,
    slot: `label-${level + 1}`,
  })),
);
const damageLevel = ref<number | null>(null);

const allLoading = computed(
  () => imageLoading.value || annotationStore.overlapLoading || annotatorLoading.value,
);

function initializeViewer() {
  if (!annotationStore.selectedImageUrl) return;

  imageLoading.value = true;
  annotatorLoading.value = true;

  void nextTick(() => {
    const container = document.getElementById('openseadragon-container');
    if (!container) return;
    // console.log('Initializing OpenSeadragon for image:', annotationStore.selectedImageUrl);

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
        navigatorPosition: 'BOTTOM_LEFT',
        navigatorSizeRatio: 0.2,
        preload: true,
      });

      const navigatorStyle = (document.getElementsByClassName('navigator')[0] as HTMLElement).style;
      navigatorStyle.background = 'white';
      navigatorStyle.opacity = '1';
      navigatorStyle.border = '1px solid #ccc';

      viewer.addHandler('open', () => {
        imageLoading.value = false;
      });

      selectedAnnotationId.value = null;

      annotator = createOSDAnnotator(viewer, {
        autoSave: true,
        drawingEnabled: isDrawingMode.value,
      });

      annotator.setDrawingTool('polygon');
      damageLevel.value = null;

      annotator.on('createAnnotation', (annotation: unknown) => {
        // console.log('Created annotation:', annotation);
        damageLevel.value = 0;
        (annotation as Annotation).bodies.push({
          purpose: 'damage',
          value: damageLevel.value.toString(),
        });

        annotationStore
          .addAnnotation(annotationStore.selectedImageUrl!, annotation as Annotation)
          .catch((error) => {
            console.error('Failed to add annotation:', error);
            Notify.create({
              type: 'negative',
              message: t('failedToAddAnnotation'),
            });
          });
      });

      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      annotator.on('updateAnnotation', (annotation: unknown, previous: unknown) => {
        // console.log('Updated annotation:', annotation, 'Previous:', previous);
        annotationStore
          .updateAnnotation(annotationStore.selectedImageUrl!, annotation as Annotation)
          .catch((error) => {
            console.error('Failed to update annotation:', error);
            Notify.create({
              type: 'negative',
              message: t('failedToUpdateAnnotation'),
            });
          });
      });

      annotator.on('deleteAnnotation', (annotation: unknown) => {
        // console.log('Deleted annotation:', annotation);
        annotationStore
          .deleteAnnotation(annotationStore.selectedImageUrl!, annotation as Annotation)
          .catch((error) => {
            console.error('Failed to delete annotation:', error);
            Notify.create({
              type: 'negative',
              message: t('failedToDeleteAnnotation'),
            });
          });
        damageLevel.value = null;
      });

      annotator.on('selectionChanged', (selected: unknown[]) => {
        if (selected.length === 0) {
          selectedAnnotationId.value = null;
          damageLevel.value = null;
        } else {
          const annotation = selected[0] as Annotation;
          selectedAnnotationId.value = annotation.id;
          const level = parseInt(annotation.bodies[0]!.value);
          damageLevel.value = level === 0 ? null : level;
        }
      });

      annotatorLoading.value = false;
    } catch (error) {
      console.error('Error initializing OpenSeadragon:', error);
      $q.dialog({
        title: t('errorLoadingImageTitle'),
        message: t('errorLoadingImageMessage'),
        color: 'negative',
        persistent: true,
        ok: true,
      });
    }
  });
}

function setExistingAnnotations() {
  if (!annotator) return;

  if (annotator.getAnnotations().length == 0) {
    const existingAnnotations = annotationStore.getAnnotationsForImage(
      annotationStore.selectedImageUrl!,
    );

    if (existingAnnotations.length) {
      annotator.setAnnotations(existingAnnotations);
    }
  }

  annotator.setStyle(
    // @ts-expect-error - Typing too complex
    (annotation: Annotation, state?: { selected: boolean; hovered: boolean }) => {
      if (!state) return;
      if (!annotation.bodies[0]) return;

      const damageLevel = parseInt(annotation.bodies[0].value);
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

  annotator.removeAnnotation(selectedAnnotationId.value); // trigger deleteAnnotation event
  selectedAnnotationId.value = null;
}

function updateDamageLevel(newLevel: number | null) {
  if (!annotator || !selectedAnnotationId.value) return;

  const effectiveLevel = newLevel ?? 0;
  const annotation = annotator.getAnnotationById(selectedAnnotationId.value) as Annotation;
  annotation.bodies[0]!.value = effectiveLevel.toString();
  annotationStore
    .updateAnnotation(annotationStore.selectedImageUrl!, annotation)
    .then(() => {
      annotator?.setSelected(annotation.id);
    })
    .catch((error) => {
      console.error('Failed to update damage level:', error);
      Notify.create({
        type: 'negative',
        message: t('failedToUpdateDamageLevel'),
      });
    });
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

watch(
  () => allLoading.value,
  (isLoading) => {
    if (isLoading) return;
    setExistingAnnotations();
  },
);

onUnmounted(() => {
  destroyViewer();
});

onMounted(() => {
  if (annotationStore.selectedImageUrl) {
    initializeViewer();
  }
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

.viewer-controls {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 8px;
}

.damage-levels {
  outline: 1px solid $primary !important;
}

:deep(.damage-levels .q-btn) {
  padding: 5px !important;
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
