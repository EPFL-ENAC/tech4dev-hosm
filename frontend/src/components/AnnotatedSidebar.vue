<template>
  <div class="annotated-sidebar">
    <div class="sidebar-header q-pl-md q-pt-md q-pb-sm">
      <div class="text-h6">{{ t('sidebarTitle') }}</div>
      <div class="text-caption text-grey">
        {{ t('image', annotationStore.annotatedImages.length) }}
      </div>
    </div>

    <div class="sidebar-content" ref="sidebarContent">
      <q-table
        :rows="reversedImages"
        :columns="columns"
        :rows-per-page-options="[20, 50, 100]"
        :rows-per-page-label="t('itemsPerPage')"
        row-key="imageUrl"
        flat
        bordered
        @row-click="selectImage"
      >
        <template v-slot:header-cell-name="props">
          <q-th :props="props" class="header-cell">
            <q-icon name="text_fields" size="20px" class="header-icon" />
          </q-th>
        </template>
        <template v-slot:header-cell-annotationsCount="props">
          <q-th :props="props" class="header-cell">
            <q-icon name="sym_r_polyline" size="20px" class="header-icon" />
          </q-th>
        </template>
        <template v-slot:header-cell-completed="props">
          <q-th :props="props" class="header-cell">
            <q-icon name="check" size="20px" class="header-icon" />
          </q-th>
        </template>

        <template v-slot:body-cell-thumbnail="props">
          <q-td
            :props="props"
            class="cursor-pointer"
            :class="{
              'bg-secondary text-white': annotationStore.selectedImageUrl === props.row.imageUrl,
            }"
          >
            <q-icon name="image" size="24px" style="transform: translateX(-4px)" />
          </q-td>
        </template>
        <template v-slot:body-cell-name="props">
          <q-td
            :props="props"
            class="image-url cursor-pointer"
            :class="{ 'text-bold': annotationStore.selectedImageUrl === props.row.imageUrl }"
          >
            {{ getImageName(props.row.imageUrl) }}
          </q-td>
        </template>
        <template v-slot:body-cell-annotationsCount="props">
          <q-td :props="props">
            {{ props.row.annotations.length }}
          </q-td>
        </template>
        <template v-slot:body-cell-completed="props">
          <q-td :props="props">
            <q-icon v-if="props.row.completed" name="check" color="positive" size="20px" />
          </q-td>
        </template>
        <template v-slot:body-cell-actions="props">
          <q-td :props="props">
            <q-btn
              flat
              dense
              round
              icon="delete"
              color="negative"
              class="image-list-delete-btn"
              @click.stop="confirmDelete(props.row.imageUrl)"
            />
          </q-td>
        </template>
        <template v-slot:no-data>
          <div class="full-width text-grey text-center q-pa-md">
            {{ t('noImages') }}
          </div>
        </template>

        <template #pagination="scope">
          <div class="row items-center">
            <q-btn
              v-if="scope.pagesNumber > 2"
              icon="first_page"
              color="grey-8"
              round
              dense
              flat
              :disable="scope.isFirstPage"
              @click="scope.firstPage"
            />
            <q-btn
              icon="chevron_left"
              color="grey-8"
              round
              dense
              flat
              :disable="scope.isFirstPage"
              @click="scope.prevPage"
            />
            <span class="q-mx-md">
              {{ t('page') }} {{ scope.pagination.page }} {{ t('of') }} {{ scope.pagesNumber }}
            </span>
            <q-btn
              icon="chevron_right"
              color="grey-8"
              round
              dense
              flat
              :disable="scope.isLastPage"
              @click="scope.nextPage"
            />
            <q-btn
              v-if="scope.pagesNumber > 2"
              icon="last_page"
              color="grey-8"
              round
              dense
              flat
              :disable="scope.isLastPage"
              @click="scope.lastPage"
            />
          </div>
        </template>
      </q-table>
    </div>

    <div class="sidebar-footer q-pa-md">
      <q-btn
        v-if="!imageCompleted"
        color="green"
        :label="t('markAsCompleted')"
        icon="check"
        unelevated
        no-caps
        class="full-width"
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
        class="full-width"
        @click="markAsIncomplete"
      />
      <q-btn
        v-if="!reviewMode"
        color="primary"
        :label="t('annotateNew')"
        icon="add"
        unelevated
        no-caps
        class="full-width q-mt-sm"
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
import type { AnnotatedImage } from '../models';

const props = defineProps<{
  annotatorId?: number | undefined;
}>();
const reviewMode = computed(() => props.annotatorId !== undefined);

const { t } = useI18n();
const annotationStore = useAnnotationDataStore();
const datasetStore = useDatasetImagesStore();
const $q = useQuasar();

const skipDeleteConfirmation = ref(false);
const sidebarContentRef = useTemplateRef('sidebarContent');
const imageCompleted = computed(() => annotationStore?.selectedImage?.completed);
const reversedImages = computed(() => [...annotationStore.annotatedImages].reverse());

const columns = [
  {
    name: 'thumbnail',
    label: '',
    field: 'thumbnail',
    align: 'center' as const,
    sortable: false,
    headerStyle: 'width: 30px;',
  },
  {
    name: 'name',
    label: '',
    field: 'name',
    align: 'left' as const,
    sortable: true,
    headerStyle: 'width: min-content;',
    style: 'text-overflow: ellipsis; overflow: hidden;',
  },
  {
    name: 'annotationsCount',
    label: '',
    field: 'annotationsCount',
    align: 'center' as const,
    sortable: true,
    headerStyle: 'width: 10px;',
  },
  {
    name: 'completed',
    label: '',
    field: 'completed',
    align: 'center' as const,
    sortable: true,
    headerStyle: 'width: 10px;',
  },
  {
    name: 'actions',
    label: '',
    field: 'actions',
    align: 'center' as const,
    headerStyle: 'width: 10px;',
  },
];

function scrollToBottom() {
  nextTick(() => {
    if (sidebarContentRef.value) {
      sidebarContentRef.value.scrollTop = sidebarContentRef.value.scrollHeight;
    }
  }).catch((err) => {
    console.error('Failed to scroll sidebar:', err);
  });
}

function selectImage(_evt: Event, row: AnnotatedImage) {
  annotationStore.setSelectedImageUrl(row.imageUrl);
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

onMounted(async () => {
  if (annotationStore.annotatedImages.length === 0 || reviewMode) {
    await annotationStore.loadAnnotations(props.annotatorId);
  }
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
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.sidebar-footer {
}

.q-table__container {
  border: none;
  height: 100%;
}

:deep(table) {
  width: 100% !important;
  table-layout: fixed !important;

  thead tr th {
    background-color: white;
    position: sticky;
    z-index: 1;
    top: 0;
  }

  .q-icon {
    margin: 0;
  }
}

:deep(.q-table__middle) {
  overflow-x: hidden !important;
}

.image-list-delete-btn {
  transform: translateX(-11px);
}
</style>
