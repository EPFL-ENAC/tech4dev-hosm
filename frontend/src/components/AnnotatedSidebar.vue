<template>
  <div class="annotated-sidebar">
    <div class="sidebar-header q-pl-md q-pt-md q-pb-sm">
      <div class="text-h6">{{ t('sidebarTitle') }}</div>
      <div class="text-caption text-grey">
        {{ t('image', annotationStore.annotatedImages.length) }}
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
            <q-avatar
              size="40px"
              :color="image.completed ? 'secondary' : 'grey-6'"
              text-color="white"
            >
              <q-icon :name="image.completed ? 'check' : 'image'" size="20px" />
            </q-avatar>
          </q-item-section>

          <q-item-section>
            <q-item-label class="image-url">
              {{ getImageName(image.imageUrl) }}
            </q-item-label>
            <q-item-label caption>
              {{ t('annotation', { n: image.annotations.length }) }}
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
            <q-item-label class="text-grey text-center">{{ t('noImages') }}</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </div>

    <div class="sidebar-footer q-pa-md">
      <q-btn
        v-if="!imageCompleted"
        color="secondary"
        :label="t('markAsCompleted')"
        icon="check"
        unelevated
        no-caps
        class="full-width q-mb-md"
        :disable="!annotationStore.selectedImageUrl"
        @click="markAsCompleted"
      />
      <q-btn
        v-else
        color="grey-7"
        :label="t('markAsIncomplete')"
        icon="close"
        unelevated
        no-caps
        class="full-width q-mb-md"
        @click="markAsIncomplete"
      />
      <div class="row q-col-gutter-sm">
        <div class="col-6">
          <q-btn
            color="grey-8"
            icon="arrow_back"
            size="sm"
            outline
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
            no-caps
            :disable="!canNavigateNext"
            @click="annotationStore.selectNext()"
            class="full-width"
          />
        </div>
      </div>
      <q-btn
        color="primary"
        :label="t('annotateNew')"
        icon="add"
        unelevated
        no-caps
        class="full-width q-mt-md"
        @click="annotateNew"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, useTemplateRef, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { useDatasetImagesStore } from 'stores/dataset-images';
import { useQuasar, Notify } from 'quasar';
import ImageDeleteConfirmDialog from './ImageDeleteConfirmDialog.vue';

const { t } = useI18n();
const annotationStore = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();
const $q = useQuasar();

const skipDeleteConfirmation = ref(false);
const sidebarContentRef = useTemplateRef('sidebarContent');
const imageCompleted = computed(() => annotationStore?.selectedImage?.completed);

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

async function annotateNew() {
  const [nextUrl, overlapPromise] = datasetStore.getNextImageInfo();

  if (!nextUrl) {
    Notify.create({
      type: 'info',
      message: t('noMoreImages'),
    });
    return;
  }

  await annotationStore.addImage(nextUrl);
  annotationStore.overlapsLoading[nextUrl] = overlapPromise !== null;
  annotationStore.setSelectedImageUrl(nextUrl);
  overlapPromise
    ?.then((overlap) => annotationStore.addAnnotationsFromOverlap(nextUrl, overlap))
    .then(() => {
      annotationStore.overlapsLoading[nextUrl] = false;
    })
    .catch((err) => {
      console.error('Failed to load overlap data:', err);
      annotationStore.overlapsLoading[nextUrl] = false;
    });
  scrollToBottom();
}

function getImageName(url: string): string {
  try {
    const urlObj = new URL(url);
    const pathParts = urlObj.pathname.split('/');
    const filename = pathParts[pathParts.length - 1];
    const nameWithoutExtension = filename?.split('.').slice(0, -1).join('.');
    return nameWithoutExtension || url;
  } catch {
    return url;
  }
}

async function markAsCompleted() {
  if (annotationStore.selectedImage) {
    await annotationStore.updateImageCompleted(annotationStore.selectedImage.imageUrl, true);
  }
}

async function markAsIncomplete() {
  if (annotationStore.selectedImage) {
    await annotationStore.updateImageCompleted(annotationStore.selectedImage.imageUrl, false);
  }
}

async function confirmDelete(imageUrl: string) {
  if (skipDeleteConfirmation.value) {
    const wasSelected = annotationStore.selectedImageUrl === imageUrl;
    await annotationStore.removeImage(imageUrl);
    if (!datasetStore.preloadedImageUrl) datasetStore.preloadNextImage();

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
      title: t('deleteImage'),
      message: t('deleteImageMessage'),
    },
  }).onOk((shouldRemember: boolean) => {
    if (shouldRemember) {
      skipDeleteConfirmation.value = true;
    }

    const wasSelected = annotationStore.selectedImageUrl === imageUrl;
    annotationStore
      .removeImage(imageUrl)
      .then(() => {
        if (!datasetStore.preloadedImageUrl) datasetStore.preloadNextImage();

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
      })
      .catch((err) => {
        console.error('Failed to delete image:', err);
        Notify.create({
          type: 'negative',
          message: t('deleteImageFailed'),
        });
      });
  });
}

onMounted(() => {
  datasetStore.preloadNextImage();
});
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
