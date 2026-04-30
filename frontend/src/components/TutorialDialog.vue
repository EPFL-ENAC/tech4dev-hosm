<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="q-dialog-plugin tutorial-dialog">
      <q-card-section>
        <div class="text-h6">{{ t('tutorialTitle') }}</div>
      </q-card-section>

      <q-card-section class="q-pa-none">
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
          class="tutorial-carousel"
        >
          <q-carousel-slide
            v-for="(step, index) in steps"
            :key="index"
            :name="index"
            class="column no-wrap flex-center q-pa-md"
          >
            <q-video
              :src="step.image"
              :alt="`Tutorial step ${index + 1}`"
              class="tutorial-image"
              draggable="false"
            />
            <div class="tutorial-text q-pa-md text-center">
              {{ step.text }}
            </div>
          </q-carousel-slide>
        </q-carousel>
      </q-card-section>

      <q-card-actions align="center">
        <q-btn
          flat
          :label="t(isLastStep ? 'finish' : 'close')"
          color="primary"
          @click="onCloseClick"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
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
</script>

<style scoped>
.tutorial-carousel {
  height: 400px;
  max-height: 70vh;
}

.tutorial-image {
  max-width: 100%;
  max-height: 250px;
  object-fit: contain;
}

.tutorial-text {
  font-size: 1rem;
  line-height: 1.5;
}
</style>
