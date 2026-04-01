<template>
  <div class="annotated-sidebar">
    <div class="sidebar-header q-pl-md q-pt-md q-pb-sm">
      <div class="text-h6">Annotated images</div>
      <div class="text-caption text-grey">
        {{ annotationStore.annotatedImages.length }} image{{
          annotationStore.annotatedImages.length > 1 ? 's' : ''
        }}
      </div>
    </div>

    <div class="sidebar-content" ref="sidebarContent">
      <q-list class="image-list">
        <q-item
          v-for="image of annotationStore.annotatedImages"
          :key="image.imageUrl"
          ref="imageItems"
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
            <q-item-label caption>
              {{ image.annotations.length }} annotation{{ image.annotations.length > 1 ? 's' : '' }}
            </q-item-label>
          </q-item-section>

          <q-item-section side>
            <q-btn
              flat
              dense
              round
              icon="delete"
              color="negative"
              class="image-list-delete-btn"
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
    </div>

    <div class="sidebar-footer q-pa-md">
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, useTemplateRef } from 'vue';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { useDatasetImagesStore } from 'stores/dataset-images';
import { useQuasar } from 'quasar';
import ImageDeleteConfirmDialog from './ImageDeleteConfirmDialog.vue';

const annotationStore = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();
const $q = useQuasar();

const skipDeleteConfirmation = ref(false);
const sidebarContentRef = useTemplateRef('sidebarContent');

function scrollToBottom() {
  nextTick(() => {
    if (sidebarContentRef.value) {
      sidebarContentRef.value.scrollTop = sidebarContentRef.value.scrollHeight;
    }
  }).catch((err) => {
    console.error('Failed to scroll sidebar:', err);
  });
}

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
  const [nextUrl, overlapPromise] = datasetStore.getNextImageInfo();

  if (!nextUrl) {
    console.warn('All images have been annotated or no images available');
    return;
  }

  annotationStore.overlapLoading = overlapPromise !== null;
  annotationStore.addImage(nextUrl);
  annotationStore.setSelectedImageUrl(nextUrl);
  overlapPromise
    ?.then((overlap) => {
      annotationStore.addAnnotationsFromOverlap(nextUrl, overlap);
      annotationStore.overlapLoading = false;
    })
    .catch((err) => {
      console.error('Failed to load overlap data:', err);
      annotationStore.overlapLoading = false;
    });
  scrollToBottom();
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
  height: 100%;
}

.sidebar-header {
  flex-shrink: 0;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.image-list-delete-btn {
  margin-right: -10px;
}

.sidebar-footer {
  flex-shrink: 0;
}

.image-url {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
