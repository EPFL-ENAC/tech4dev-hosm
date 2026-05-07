<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="q-dialog-plugin tutorial-dialog q-pa-sm">
      <q-card-section>
        <div class="text-h6">{{ t('tutorialTitle') }}</div>
      </q-card-section>

      <q-card-actions align="center">
        <q-btn :label="t('skip')" color="grey-7" flat no-caps @click="onCloseClick" />
        <q-btn :label="t('start')" color="primary" unelevated no-caps @click="startTour" />
        <LanguageSelector />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { useDialogPluginComponent } from 'quasar';
import LanguageSelector from 'components/LanguageSelector.vue';

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogCancel } = useDialogPluginComponent();
import { useShepherd } from 'vue-shepherd';

function onCloseClick() {
  onDialogCancel();
}

function startTour() {
  const tour = useShepherd({
    useModalOverlay: true,
    defaultStepOptions: {
      cancelIcon: {
        enabled: true,
      },
    },
  });

  tour.addStep({
    attachTo: { element: '.annotate-new-btn', on: 'right' },
    text: t('tutorialSteps.0'),
    buttons: [
      {
        text: t('skip'),
        action: tour.cancel,
        secondary: true,
      },
      {
        text: t('next'),
        action: tour.next,
      },
    ],
  });

  tour.addStep({
    attachTo: { element: '.add-annotation-btn', on: 'bottom' },
    text: t('tutorialSteps.1'),
    buttons: [
      {
        text: t('back'),
        action: tour.back,
        secondary: true,
      },
      {
        text: t('next'),
        action: tour.next,
      },
    ],
  });

  tour.addStep({
    attachTo: { element: '#openseadragon-container', on: 'center' },
    text: t('tutorialSteps.2'),
    buttons: [
      {
        text: t('back'),
        action: tour.back,
        secondary: true,
      },
      {
        text: t('next'),
        action: tour.next,
      },
    ],
  });

  tour.addStep({
    attachTo: { element: '.damage-level-btns', on: 'bottom' },
    text: t('tutorialSteps.3'),
    buttons: [
      {
        text: t('back'),
        action: tour.back,
        secondary: true,
      },
      {
        text: t('next'),
        action: tour.next,
      },
    ],
  });

  tour.addStep({
    attachTo: { element: '.reference-map-btn', on: 'bottom' },
    text: t('tutorialSteps.4'),
    buttons: [
      {
        text: t('back'),
        action: tour.back,
        secondary: true,
      },
      {
        text: t('next'),
        action: tour.next,
      },
    ],
  });

  tour.addStep({
    attachTo: { element: '.mark-completed-btn', on: 'right' },
    text: t('tutorialSteps.5'),
    buttons: [
      {
        text: t('back'),
        action: tour.back,
        secondary: true,
      },
      {
        text: t('finish'),
        action: tour.complete,
      },
    ],
  });

  onDialogCancel();
  tour.start();
}
</script>

<style lang="scss">
.q-card__actions .q-btn--rectangle {
  padding: $button-padding;
}

.shepherd-element {
  max-width: 400px;
  border: none;
  border-radius: 6px;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.2);
}

.shepherd-text {
  padding: 0.5rem;
  font-size: 0.95rem;
  line-height: 1.5;
}

.shepherd-footer {
  padding: 0 0.5rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.shepherd-button {
  padding: $button-padding;
  border-radius: 6px;
  border: none;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;

  &:not(.shepherd-button-secondary) {
    background: var(--q-primary);
    color: white;

    &:hover {
      opacity: 0.9;
    }
  }

  &.shepherd-button-secondary {
    background: transparent;
    color: #666;

    &:hover {
      background: #f5f5f5;
    }
  }
}

.shepherd-modal-overlay-container {
  z-index: 9998;
}

.shepherd-element {
  z-index: 9999;
}
</style>
