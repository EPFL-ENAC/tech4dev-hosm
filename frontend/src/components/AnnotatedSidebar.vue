<template>
  <div class="annotated-sidebar q-pl-lg" style="height: 100%">
    <q-card flat class="column" style="height: 100%">
      <q-card-section>
        <div class="text-h6">Annotated images</div>
        <div class="text-caption text-grey">
          {{ annotationStore.annotatedImages.length }} image{{
            annotationStore.annotatedImages.length > 1 ? 's' : ''
          }}
        </div>
      </q-card-section>

      <q-list class="image-list scroll" style="flex: 1 1 auto">
        <q-item
          v-for="image in annotationStore.annotatedImages"
          :key="image.imageUrl"
          clickable
          :active="annotationStore.selectedImageUrl === image.imageUrl"
          @click="selectImage(image.imageUrl)"
        >
          <q-item-section avatar>
            <q-avatar size="40px" color="secondary" text-color="white">
              <q-icon name="image" />
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

        <q-item v-if="annotationStore.annotatedImages.length === 0">
          <q-item-section>
            <q-item-label class="text-grey text-center">No images yet</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>

      <q-card-section class="q-pt-none">
        <div class="row q-col-gutter-sm">
          <div class="col-6">
            <q-btn
              color="grey-8"
              icon="arrow_back"
              size="sm"
              outline
              square
              no-caps
              :disable="!canNavigatePrevious"
              @click="annotationStore.selectPrevious()"
              class="full-width"
            />
          </div>
          <div class="col-6">
            <q-btn
              color="grey-8"
              icon="arrow_forward"
              size="sm"
              outline
              square
              no-caps
              :disable="!canNavigateNext"
              @click="annotationStore.selectNext()"
              class="full-width"
            />
          </div>
        </div>
        <q-btn
          color="primary"
          label="Annotate new"
          icon="add"
          unelevated
          square
          no-caps
          class="full-width q-mt-sm"
          @click="annotateNew"
        />
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { useDatasetImagesStore } from 'stores/dataset-images';
import { useQuasar } from 'quasar';
import ImageDeleteConfirmDialog from './ImageDeleteConfirmDialog.vue';

const annotationStore = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();
const $q = useQuasar();

const skipDeleteConfirmation = ref(false);

const canNavigatePrevious = computed(() => {
  const currentIndex = annotationStore.annotatedImages.findIndex(
    (img) => img.imageUrl === annotationStore.selectedImageUrl,
  );
  return currentIndex > 0;
});

const canNavigateNext = computed(() => {
  const currentIndex = annotationStore.annotatedImages.findIndex(
    (img) => img.imageUrl === annotationStore.selectedImageUrl,
  );
  return currentIndex >= 0 && currentIndex < annotationStore.annotatedImages.length - 1;
});

function selectImage(url: string) {
  annotationStore.setSelectedImageUrl(url);
}

function annotateNew() {
  const annotatedUrls = annotationStore.annotatedImages.map((img) => img.imageUrl);

  const nextUrl = datasetStore.getNextImageUrl(annotatedUrls);

  if (!nextUrl) {
    console.warn('All images have been annotated or no images available');
    return;
  }

  annotationStore.addImage(nextUrl);
  annotationStore.setSelectedImageUrl(nextUrl);
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
  if (skipDeleteConfirmation.value) {
    const wasSelected = annotationStore.selectedImageUrl === imageUrl;
    annotationStore.removeImage(imageUrl);

    if (annotationStore.annotatedImages.length > 0) {
      if (wasSelected) {
        const lastImage =
          annotationStore.annotatedImages[annotationStore.annotatedImages.length - 1];
        if (lastImage) {
          annotationStore.setSelectedImageUrl(lastImage.imageUrl);
        }
      }
    } else {
      annotationStore.setSelectedImageUrl(null);
    }
    return;
  }

  $q.dialog({
    component: ImageDeleteConfirmDialog,
    componentProps: {
      title: 'Delete Image',
      message:
        'Are you sure you want to delete this image? This will also delete all annotation data for this image. This action cannot be undone.',
    },
  }).onOk((shouldRemember: boolean) => {
    if (shouldRemember) {
      skipDeleteConfirmation.value = true;
    }

    const wasSelected = annotationStore.selectedImageUrl === imageUrl;
    annotationStore.removeImage(imageUrl);

    if (annotationStore.annotatedImages.length > 0) {
      if (wasSelected) {
        const lastImage =
          annotationStore.annotatedImages[annotationStore.annotatedImages.length - 1];
        if (lastImage) {
          annotationStore.setSelectedImageUrl(lastImage.imageUrl);
        }
      }
    } else {
      annotationStore.setSelectedImageUrl(null);
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
