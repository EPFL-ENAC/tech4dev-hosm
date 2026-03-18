<template>
  <div class="annotated-sidebar q-pa-md">
    <q-card flat>
      <q-card-section>
        <div class="text-h6">Annotated Images</div>
        <div class="text-caption text-grey">
          {{ store.annotatedImages.length }} image(s)
        </div>
      </q-card-section>

      <q-separator />

      <q-list dense class="image-list">
        <q-item
          v-for="image in store.annotatedImages"
          :key="image.imageUrl"
          clickable
          :active="store.selectedImageUrl === image.imageUrl"
          active-class="active-image-item"
          @click="selectImage(image.imageUrl)"
        >
          <q-item-section avatar>
            <q-avatar size="40px">
              <img :src="image.imageUrl" alt="Thumbnail" />
            </q-avatar>
          </q-item-section>

          <q-item-section>
            <q-item-label class="text-caption image-url">
              {{ getImageName(image.imageUrl) }}
            </q-item-label>
            <q-item-label caption>
              {{ image.annotations.length }} annotation(s)
            </q-item-label>
          </q-item-section>
        </q-item>

        <q-item v-if="store.annotatedImages.length === 0">
          <q-item-section>
            <q-item-label class="text-grey text-center">No images yet</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>

      <q-separator class="q-my-md" />

      <!-- Navigation Buttons -->
      <q-card-section class="q-pt-none">
        <div class="row q-col-gutter-sm">
          <q-btn
            color="primary"
            label="Previous"
            icon="arrow_back"
            size="sm"
            :disable="!canNavigate"
            @click="store.selectPrevious()"
          />
          <q-btn
            color="primary"
            label="Next"
            icon="arrow_forward"
            size="sm"
            :disable="!canNavigate"
            @click="store.selectNext()"
          />
        </div>
        <q-btn
          color="accent"
          label="Annotate new"
          icon="add"
          class="full-width q-mt-sm"
          @click="annotateNew"
        />
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { useDatasetImagesStore } from 'stores/dataset-images';

const store = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();

const canNavigate = computed(() => {
  return store.annotatedImages.length > 0 && store.selectedImageUrl !== null;
});

function selectImage(url: string) {
  store.setSelectedImageUrl(url);
}

function annotateNew() {
  const annotatedUrls = store.annotatedImages.map((img) => img.imageUrl);
  const randomUrl = datasetStore.getRandomImageUrl(annotatedUrls);
  if (randomUrl) {
    store.addImage(randomUrl);
  } else {
    console.warn('All images have been annotated or no images available');
  }
}

function getImageName(url: string): string {
  try {
    const urlObj = new URL(url);
    const pathParts = urlObj.pathname.split('/');
    return pathParts[pathParts.length - 1] || url;
  } catch {
    return url;
  }
}
</script>

<style scoped lang="scss">
.image-list {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 250px);
}

.active-image-item {
  background: rgba($primary, 0.1);
}

.image-url {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
