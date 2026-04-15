<template>
  <q-page class="annotation-page">
    <q-card class="main-frame">
      <q-card-section v-if="annotationStore.selectedImage" class="map-section">
        <AnnotatedMap />
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
import { useAnnotationDataStore } from 'stores/annotation-data';
import AnnotatedMap from 'components/AnnotatedMap.vue';

const annotationStore = useAnnotationDataStore();
</script>

<style scoped lang="scss">
.map-section {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
