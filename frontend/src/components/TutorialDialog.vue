<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="q-dialog-plugin tutorial-dialog">
      <q-card-section>
        <div class="text-h6">Tutorial</div>
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
            <img
              :src="`/tutorial_${index + 1}.webp`"
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
          :label="isLastStep ? 'Finish' : 'Close'"
          color="primary"
          @click="onCloseClick"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useDialogPluginComponent } from 'quasar';
// import tutorialSteps from '../assets/tutorial-steps.json';
const tutorialSteps = [
  {
    image: 'tutorial_1.webp',
    text: 'Get a new image to annotate by clicking the "Annotate New" button in the sidebar.',
  },
  {
    image: 'tutorial_2.webp',
    text: 'Use the annotation tools to draw bounding boxes around buildings and set an appropriate damage level for each building.',
  },
  {
    image: 'tutorial_3.webp',
    text: 'Use the "Export Annotations" button to download your annotations as a JSON file.',
  },
];

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogCancel } = useDialogPluginComponent();

const steps = tutorialSteps;
const slide = ref(0);
const isLastStep = computed(() => slide.value === steps.length - 1);

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
