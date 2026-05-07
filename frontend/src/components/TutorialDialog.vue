<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide" class="tutorial-dialog-wrapper">
    <q-card class="q-dialog-plugin tutorial-dialog column no-wrap">
      <q-card-section class="row">
        <div class="text-h6">{{ t('tutorialTitle') }}</div>
      </q-card-section>

      <q-card-section class="col-grow row no-wrap q-pa-none">
        <q-carousel
          v-model="slide"
          transition-prev="slide-right"
          transition-next="slide-left"
          swipeable
          animated
          arrows
          control-type="flat"
          control-color="primary"
          navigation
          class="tutorial-carousel column"
        >
          <q-carousel-slide
            v-for="(step, index) in steps"
            :key="index"
            :name="index"
            class="column no-wrap q-pa-md"
          >
            <q-video
              :src="step.image"
              :alt="`Tutorial step ${index + 1}`"
              class="tutorial-image"
              draggable="false"
            />
            <div class="tutorial-text q-pa-md text-center" v-html="step.text"></div>
          </q-carousel-slide>
        </q-carousel>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn
          v-if="!isLastStep"
          :label="t('skip')"
          color="grey-7"
          flat
          no-caps
          @click="onCloseClick"
        />
        <q-btn
          color="primary"
          unelevated
          no-caps
          :label="t(isLastStep ? 'finish' : 'next')"
          @click="isLastStep ? onCloseClick() : next()"
        />
        <LanguageSelector />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import LanguageSelector from 'components/LanguageSelector.vue';
const tm = (() => {
  const i18n = useI18n();
  return (key: string) => i18n.tm(key);
})();
import { useDialogPluginComponent } from 'quasar';

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogCancel } = useDialogPluginComponent();

const steps = computed(() =>
  (tm('tutorialSteps') as string[]).map((step, index) => ({
    image: `tutorial_${index + 1}.mp4`,
    text: step,
  })),
);
const slide = ref(0);
const isLastStep = computed(() => slide.value === steps.value.length - 1);

function onCloseClick() {
  onDialogCancel();
}

function next() {
  slide.value++;
}
</script>

<style lang="scss" scoped>
.tutorial-dialog-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
}

.tutorial-dialog {
  width: 90vw;
  max-width: 1200px;
  height: 90vh;
  max-height: 800px;
}

.tutorial-carousel {
  height: 100%;
  width: 100%;
}

.tutorial-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.tutorial-text {
  font-size: 1rem;
  line-height: 1.5;
}

:deep(.q-carousel__control) {
  transform: translateY(20px);
}

.q-card__actions .q-btn--rectangle {
  padding: $button-padding;
}
</style>
