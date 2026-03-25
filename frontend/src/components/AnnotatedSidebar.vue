<template>
  <div class="annotated-sidebar q-pl-lg" style="height: 100%">
    <q-card flat class="column" style="height: 100%">
      <q-card-section>
        <div class="text-h6">Annotated images</div>
        <div class="text-caption text-grey">
          {{ store.annotatedImages.length }} image{{ store.annotatedImages.length > 1 ? 's' : '' }}
        </div>
      </q-card-section>

      <q-list class="image-list scroll" style="flex: 1 1 auto">
        <q-item
          v-for="image in store.annotatedImages"
          :key="image.imageUrl"
          clickable
          :active="store.selectedImageUrl === image.imageUrl"
          @click="selectImage(image.imageUrl)"
        >
          <q-item-section avatar>
            <q-avatar size="40px">
              <img :src="image.imageUrl" alt="Thumbnail" />
            </q-avatar>
          </q-item-section>

          <q-item-section>
            <q-item-label class="image-url">
              {{ getImageName(image.imageUrl) }}
            </q-item-label>
            <q-item-label caption> {{ image.annotations.length }} annotation(s) </q-item-label>
          </q-item-section>

          <q-item-section side>
            <q-btn
              flat
              dense
              round
              icon="delete"
              color="negative"
              @click.stop="confirmDelete(image.imageUrl)"
            />
          </q-item-section>
        </q-item>

        <q-item v-if="store.annotatedImages.length === 0">
          <q-item-section>
            <q-item-label class="text-grey text-center">No images yet</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>

      <q-card-section class="q-pt-none">
        <div class="row q-col-gutter-sm">
          <div class="col-6">
            <q-btn
              color="accent"
              label="Previous"
              icon="arrow_back"
              size="sm"
              :disable="!canNavigatePrevious"
              @click="store.selectPrevious()"
              class="full-width"
            />
          </div>
          <div class="col-6">
            <q-btn
              color="accent"
              label="Next"
              icon="arrow_forward"
              size="sm"
              :disable="!canNavigateNext"
              @click="store.selectNext()"
              class="full-width"
            />
          </div>
        </div>
        <q-btn
          color="secondary"
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
import { useQuasar } from 'quasar';

const store = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();
const $q = useQuasar();

const canNavigatePrevious = computed(() => {
  const currentIndex = store.annotatedImages.findIndex(
    (img) => img.imageUrl === store.selectedImageUrl,
  );
  return currentIndex > 0;
});

const canNavigateNext = computed(() => {
  const currentIndex = store.annotatedImages.findIndex(
    (img) => img.imageUrl === store.selectedImageUrl,
  );
  return currentIndex >= 0 && currentIndex < store.annotatedImages.length - 1;
});

function selectImage(url: string) {
  store.setSelectedImageUrl(url);
}

function annotateNew() {
  const annotatedUrls = store.annotatedImages.map((img) => img.imageUrl);
  const randomUrl = datasetStore.getRandomImageUrl(annotatedUrls);
  if (randomUrl) {
    const beforeCount = store.annotatedImages.length;
    store.addImage(randomUrl);
    if (store.annotatedImages.length > beforeCount) {
      store.setSelectedImageUrl(randomUrl);
    }
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

function confirmDelete(imageUrl: string) {
  $q.dialog({
    title: 'Delete Image',
    message:
      'Are you sure you want to delete this image? This will also delete all annotation data for this image. This action cannot be undone.',
    cancel: true,
    persistent: true,
  }).onOk(() => {
    const wasSelected = store.selectedImageUrl === imageUrl;
    store.removeImage(imageUrl);

    if (store.annotatedImages.length > 0) {
      if (wasSelected) {
        const lastImage = store.annotatedImages[store.annotatedImages.length - 1];
        if (lastImage) {
          store.setSelectedImageUrl(lastImage.imageUrl);
        }
      }
    } else {
      store.setSelectedImageUrl(null);
    }
  });
}
</script>

<style scoped lang="scss">
.annotated-sidebar {
  display: flex;
  flex-direction: column;
}

.image-list {
  overflow-y: auto;
}

.image-url {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
