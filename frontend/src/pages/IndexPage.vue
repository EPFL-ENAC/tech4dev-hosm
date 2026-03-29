<template>
  <q-page class="annotation-page">
    <!-- Main Frame -->
    <q-card class="main-frame">
      <q-card-section v-if="selectedImage" class="image-display">
        <div class="text-h6 q-mb-md">
          {{ getImageName(selectedImage.imageUrl) }}
          <span class="text-grey-6 q-ml-sm">
            ({{ selectedImage.annotations.length }} annotations)
          </span>
        </div>
        <q-img
          :src="selectedImage.imageUrl"
          alt="Selected image"
          class="image-content"
          spinner-color="primary"
        />
      </q-card-section>

      <q-card-section v-else class="empty-state">
        <div class="text-h5 text-grey-6">No annotated image</div>
        <div class="text-body1 text-grey-6 q-mt-sm">
          Use the sidebar to select an image or annotate a new one
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { useDatasetImagesStore } from 'stores/dataset-images';

const store = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();

onMounted(() => {
  void datasetStore.loadImageUrls();
});

const selectedImage = computed(() => {
  if (!store.selectedImageUrl) return null;
  return store.annotatedImages.find((img) => img.imageUrl === store.selectedImageUrl);
});

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
.annotation-page {
  height: 100%;
}

.main-frame {
  height: 100%;
}

.image-display {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.image-content {
  flex: 1;
  max-width: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
