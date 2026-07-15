<template>
  <div>
    <div class="buttons">
      <div v-if="canEdit" class="viewer-controls">
        <q-btn
          v-if="isDrawingMode"
          color="grey-8"
          no-caps
          no-wrap
          outline
          :label="t('abort')"
          icon="close"
          class="add-cancel-btn q-mr-sm"
          @click="setDrawMode(false)"
        >
          <q-tooltip>
            {{ t('escKey') }}
          </q-tooltip>
        </q-btn>
        <q-btn
          v-else
          color="primary"
          no-caps
          no-wrap
          unelevated
          :label="t('addAnnotation')"
          icon="add"
          class="add-cancel-btn q-mr-sm add-annotation-btn"
          @click="setDrawMode(true)"
        >
          <q-tooltip> N </q-tooltip>
        </q-btn>

        <q-btn
          v-if="isDrawingMode"
          color="grey-8"
          unelevated
          no-caps
          outline
          icon="undo"
          class="q-mr-sm quick-action-btn"
          @click="undoPoint()"
        >
          <q-tooltip> Ctrl+Z </q-tooltip>
        </q-btn>

        <q-btn
          v-if="isDrawingMode"
          color="green"
          unelevated
          no-caps
          outline
          icon="check"
          class="q-mr-sm quick-action-btn"
          @click="finishDrawing()"
        >
          <q-tooltip> {{ t('doubleClickOrEnter') }} </q-tooltip>
        </q-btn>

        <div v-if="selectedAnnotationId" class="damage-level-btns">
          <span
            class="text-grey q-mr-md"
            style="display: inline-block; transform: translateY(1px)"
            >{{ t('damageLevel') }}</span
          >

          <div class="damage-levels q-mr-md">
            <q-btn
              v-for="opt in damageLevelOptions.slice(1)"
              :key="opt.value"
              :style="
                damageLevel === opt.value
                  ? { background: opt.color, color: 'white' }
                  : { background: 'white', color: opt.color }
              "
              :label="opt.label"
              unelevated
              no-caps
              @click="toggleDamageLevel(opt.value)"
            >
              <q-tooltip>{{ opt.index }}</q-tooltip>
            </q-btn>
          </div>

          <q-btn
            color="grey-8"
            unelevated
            no-caps
            :label="t('circularize')"
            icon="sym_r_circle"
            outline
            :disable="!selectedAnnotationId"
            class="q-mr-md"
            @click="circularizeAnnotation()"
          >
            <q-tooltip> C </q-tooltip>
          </q-btn>

          <q-btn
            color="primary"
            unelevated
            no-caps
            :label="t('delete')"
            icon="delete"
            outline
            :disable="!selectedAnnotationId"
            class="q-mr-sm"
            @click="deleteAnnotation()"
          >
            <q-tooltip>
              {{ t('deleteKey') }}
            </q-tooltip>
          </q-btn>
        </div>

        <div v-else class="damage-level-btns q-mr-sm">
          <span class="text-grey q-mr-md">{{ t('damageLevel') }}</span>

          <div class="damage-legend">
            <div v-for="opt in damageLevelOptions" :key="opt.value" class="damage-legend-item">
              <span class="damage-legend-swatch" :style="{ background: opt.color }" />
              <span class="text-caption">{{ opt.label }}</span>
            </div>
          </div>
        </div>

        <q-btn
          v-if="fillingShown"
          color="grey-8"
          unelevated
          no-caps
          :label="t('hideFilling')"
          icon="visibility_off"
          outline
          class="q-mr-sm"
          @click="hideFilling()"
        >
          <q-tooltip>V</q-tooltip>
        </q-btn>

        <q-btn
          v-else
          color="grey-8"
          unelevated
          no-caps
          :label="t('showFilling')"
          icon="visibility"
          outline
          class="q-mr-sm"
          @click="showFilling()"
        >
          <q-tooltip>V</q-tooltip>
        </q-btn>
      </div>

      <q-btn
        color="grey-8"
        unelevated
        no-caps
        :label="t('showReferenceMap')"
        icon="map"
        outline
        v-if="!referenceMapShown"
        class="reference-map-btn"
        @click="$emit('showReferenceMap')"
      >
        <q-checkbox v-model="referenceMapShownCheckbox" dense color="grey-8" class="q-ml-sm" />
      </q-btn>
    </div>

    <div v-if="canEdit" span class="viewer-caption text-caption text-grey-7 q-mt-sm">
      <span v-if="isDrawingMode" v-html="t('captionDrawMode')" />
      <span v-else v-html="t('captionSelectMoveMode')" />
      <span v-if="selectedAnnotationId" v-html="t('captionSelected')" class="q-ml-xs" />
    </div>

    <div class="openseadragon-wrapper q-mt-sm">
      <div
        id="openseadragon-container"
        class="openseadragon-container"
        :style="isDrawingMode ? { cursor: 'crosshair' } : {}"
      />
      <q-inner-loading :showing="allLoading" transition-duration="100">
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
import {
  createOSDAnnotator,
  type OpenSeadragonAnnotator,
  type ImageAnnotation,
} from '@annotorious/openseadragon';
import { useAnnotationDataStore, DAMAGE_LEVELS, DAMAGE_COLORS } from 'stores/annotation-data';
import type { Annotation, DamageLevel } from '../models';

const ALLOW_REVIEWERS_TO_EDIT = true;

const props = defineProps<{
  referenceMapShown: boolean;
  reviewMode?: boolean;
}>();

const canEdit = computed(() => !props.reviewMode || ALLOW_REVIEWERS_TO_EDIT);

const emit = defineEmits<{
  (e: 'showReferenceMap'): void;
}>();

const { t } = useI18n();
const annotationStore = useAnnotationDataStore();
const $q = useQuasar();

let viewer: OpenSeadragon.Viewer | null = null;
let annotator: OpenSeadragonAnnotator | null = null;
const isDrawingMode = ref(false);
const viewerLoading = ref(false);
const annotatorLoading = ref(false);
const selectedAnnotationId = ref<string | null>(null);
const referenceMapShownCheckbox = ref(false);
const fastAnnotationCreation = ref(false);
const skipUpdateEvent = ref(false);
const fillingShown = ref(true);

const damageLevelOptions = computed(() =>
  DAMAGE_LEVELS.map((level, index) => ({
    label: t(`damageLevel_${level}`),
    value: level,
    index: index,
    slot: `label-${index}`,
    color: DAMAGE_COLORS[index],
  })),
);
const damageLevel = ref<DamageLevel | null>(null);

const allLoading = computed(
  () =>
    viewerLoading.value ||
    annotationStore.addingNewImage ||
    annotationStore.overlapLoading ||
    annotatorLoading.value,
);

function initializeViewer() {
  if (!annotationStore.selectedImageUrl) return;

  viewerLoading.value = true;
  annotatorLoading.value = true;

  void nextTick(() => {
    const container = document.getElementById('openseadragon-container');
    if (!container) return;
    // console.log('Initializing OpenSeadragon for image:', annotationStore.selectedImageUrl);

    const tileSourceUrl =
      annotationStore
        .selectedImageUrl!.replace('/raw-images/', '/tiles/')
        .replace(/\.[^/.]+$/, '') + '.dzi';

    try {
      viewer = OpenSeadragon({
        element: container,
        // id: 'openseadragon-container',
        prefixUrl: 'https://cdn.jsdelivr.net/gh/Benomrans/openseadragon-icons@main/images/',
        tileSources: tileSourceUrl,
        autoHideControls: false,
        gestureSettingsMouse: {
          clickToZoom: false,
        },
        crossOriginPolicy: 'Anonymous',
        showNavigator: true,
        navigatorPosition: 'BOTTOM_LEFT',
        navigatorSizeRatio: 0.2,
        // preload: true,
      });

      const navigatorStyle = (document.getElementsByClassName('navigator')[0] as HTMLElement).style;
      navigatorStyle.background = 'white';
      navigatorStyle.opacity = '1';
      navigatorStyle.border = '1px solid #ccc';

      viewer.addHandler('open', () => {
        viewerLoading.value = false;
      });

      selectedAnnotationId.value = null;

      annotator = createOSDAnnotator(viewer, {
        autoSave: true,
        drawingEnabled: isDrawingMode.value,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        userSelectAction: canEdit.value ? 'EDIT' : ('SELECT' as any),
      });

      annotator.setDrawingTool('polygon');
      annotator.setDrawingMode('click');
      damageLevel.value = null;

      annotator.on('createAnnotation', (annotation: unknown) => {
        // console.log('Created annotation:', annotation);
        setDrawMode(false);

        if (fastAnnotationCreation.value) {
          // must keep setDrawMode(false) above to properly trigger deselection
          setDrawMode(true);
          fastAnnotationCreation.value = false;
        }

        damageLevel.value = 'unset';
        (annotation as Annotation).bodies.push({
          purpose: 'damage',
          value: damageLevel.value,
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
        if (skipUpdateEvent.value) return;
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
          const level = annotation.bodies[0]!.value as DamageLevel;
          damageLevel.value = level === 'unset' ? null : level;
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
      annotator.setAnnotations(existingAnnotations as unknown as ImageAnnotation[]);
    }
  }

  setAnnotationStyle();
}

function setAnnotationStyle() {
  if (!annotator) return;

  annotator.setStyle(
    // @ts-expect-error - Typing too complex
    (annotation: Annotation, state?: { selected: boolean; hovered: boolean }) => {
      if (!state) return;
      if (!annotation.bodies[0]) return;

      const damageLevelValue = annotation.bodies[0].value as DamageLevel;
      const color = DAMAGE_COLORS[DAMAGE_LEVELS.indexOf(damageLevelValue)];
      const opacity = state.selected ? 0.2 : state.hovered ? 0.7 : 0.8;

      return {
        fill: color,
        fillOpacity: fillingShown.value ? opacity : 0,
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

function undoPoint() {
  if (annotator) {
    annotator.undoPoint();
  }
}

function finishDrawing() {
  if (annotator) {
    annotator.stopDrawing();
  }
}

async function circularizeAnnotation() {
  if (!selectedAnnotationId.value || !annotator) return;

  const updated = await annotationStore.circularizeAnnotation(
    annotationStore.selectedImageUrl!,
    selectedAnnotationId.value,
  );

  if (updated) {
    skipUpdateEvent.value = true;
    annotator.updateAnnotation(updated as unknown as ImageAnnotation);
    skipUpdateEvent.value = false;
    annotator.setSelected(selectedAnnotationId.value);
  }
}

function deleteAnnotation() {
  if (!selectedAnnotationId.value || !annotator) return;

  annotator.removeAnnotation(selectedAnnotationId.value); // trigger deleteAnnotation event
  selectedAnnotationId.value = null;
}

function toggleDamageLevel(newLevel: DamageLevel) {
  // Toggle off if clicking the same button
  const effectiveLevel = damageLevel.value === newLevel ? null : newLevel;
  damageLevel.value = effectiveLevel;
  updateDamageLevel(effectiveLevel);
}

function showFilling() {
  fillingShown.value = true;
  setAnnotationStyle();
}

function hideFilling() {
  fillingShown.value = false;
  setAnnotationStyle();
}

function updateDamageLevel(newLevel: DamageLevel | null) {
  if (!annotator || !selectedAnnotationId.value) return;

  const effectiveLevel = newLevel ?? 'unset';
  const annotation = annotator.getAnnotationById(
    selectedAnnotationId.value,
  ) as unknown as Annotation;
  annotation.bodies[0]!.value = effectiveLevel;
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
    console.log('Loading state changed. isLoading:', isLoading);
    if (isLoading) return;
    setExistingAnnotations();
  },
);

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (!isDrawingMode.value) {
      if (annotator) {
        annotator.setSelected();
      }
    } else {
      setDrawMode(false);
    }
  } else if (e.key === 'n') {
    if (isDrawingMode.value) {
      finishDrawing();
      fastAnnotationCreation.value = true;
    }
    setDrawMode(true);
  } else if (e.key === 'Enter' || e.key === 'NumpadEnter') {
    finishDrawing();
  } else if (e.key === 'c') {
    circularizeAnnotation().catch((error) => {
      console.error('Failed to circularize annotation:', error);
      Notify.create({
        type: 'negative',
        message: t('failedToCircularizeAnnotation'),
      });
    });
  } else if (e.key === 'Delete' || e.key === 'Backspace') {
    deleteAnnotation();
  } else if (e.key === 'z' && (e.ctrlKey || e.metaKey)) {
    undoPoint();
  } else if (Array.from({ length: DAMAGE_LEVELS.length }, (_, i) => i.toString()).includes(e.key)) {
    if (selectedAnnotationId.value) {
      const levelIndex = parseInt(e.key, 10);
      updateDamageLevel(DAMAGE_LEVELS[levelIndex] as DamageLevel);
    }
  } else if (e.key === 'v') {
    if (fillingShown.value) {
      hideFilling();
    } else {
      showFilling();
    }
  }
}

onMounted(() => {
  if (annotationStore.selectedImageUrl) {
    initializeViewer();
  }
  window.addEventListener('keydown', onKeyDown);
});

onUnmounted(() => {
  destroyViewer();
  window.removeEventListener('keydown', onKeyDown);
});

watch(
  () => referenceMapShownCheckbox.value,
  async (newVal) => {
    if (newVal) {
      emit('showReferenceMap');
      await nextTick(() => {
        referenceMapShownCheckbox.value = false;
      });
    }
  },
);
</script>

<style scoped lang="scss">
.annotation-page {
  height: 100%;
}

.main-frame {
  height: 100%;
  box-shadow: none;
}

.buttons {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.viewer-controls {
  flex: 1;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 8px;
}

.add-cancel-btn {
  width: 200px;
}

.quick-action-btn {
  width: 42px;
}

.reference-map-btn {
  margin-left: auto;
}

.damage-levels {
  display: inline-flex;
  outline: 1px solid $grey-4 !important;
  border-radius: 6px;
  transform: translateY(1px);
}

.damage-levels .q-btn {
  padding: 7px 16px !important;
}

.viewer-caption {
  flex-shrink: 0;
}

.openseadragon-container {
  width: 100%;
  height: calc(
    100vh - 172px
  ); // OpenSeadragon needs a height. Adjust based on header and controls height
  overflow: hidden;
}

.q-inner-loading {
  background: white;
}

.damage-legend {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  transform: translateY(2px);
}

.damage-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.damage-legend-swatch {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 2px;
  flex-shrink: 0;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
