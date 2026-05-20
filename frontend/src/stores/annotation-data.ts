import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref, computed } from 'vue';
import { baseUrl, authFetch } from 'boot/api';
import type {
  AnnotatedImage,
  AnnotationData,
  Annotation,
  Overlap,
  Point,
  AnnotatedImageRead,
  AnnotationRead,
  DamageLevel as DamageLevelType,
  ValidationStatus,
} from '../models';
import { Notify } from 'quasar';
import { getI18nT } from 'src/utils/i18n';

export const DAMAGE_LEVELS: DamageLevelType[] = ['unset', 'undamaged', 'damaged'];
export const DAMAGE_COLORS = ['#00e8d2', '#1974d2', '#ff007f'];

const OVERLAP_RATIO_THRESHOLD = 0.3;

function annotationToApi(annotation: Annotation): {
  polygon: number[][];
  damage_level: DamageLevelType;
} {
  const damageBody = annotation.bodies.find((b) => b.purpose === 'damage');
  const damageLevel = damageBody ? (damageBody.value as DamageLevelType) : 'unset';
  const polygon = annotation.target.selector.geometry.points;
  return { polygon, damage_level: damageLevel };
}

function annotationFromApi(apiAnnotation: {
  id: number;
  polygon: number[][];
  damage_level: DamageLevelType;
}): Annotation {
  return {
    id: apiAnnotation.id.toString(),
    bodies: [{ purpose: 'damage', value: apiAnnotation.damage_level }],
    target: {
      annotation: '',
      selector: {
        type: 'POLYGON',
        geometry: {
          bounds: {
            minX: Math.min(...(apiAnnotation.polygon.map((p) => p[0]) as number[])),
            maxX: Math.max(...(apiAnnotation.polygon.map((p) => p[0]) as number[])),
            minY: Math.min(...(apiAnnotation.polygon.map((p) => p[1]) as number[])),
            maxY: Math.max(...(apiAnnotation.polygon.map((p) => p[1]) as number[])),
          },
          points: apiAnnotation.polygon as Point[],
        },
      },
      creator: { isGuest: false, id: '' },
      created: new Date(),
    },
  };
}

type FetchCall = () => Promise<void>;

export const useAnnotationDataStore = defineStore('annotationData', () => {
  const userInfo = ref<AnnotationData['userInfo']>({
    fullName: '',
    email: '',
  });
  const annotatedImages = ref<AnnotatedImage[]>([]);
  const selectedImageUrl = ref<string | null>(null);
  const overlapsLoading = ref<Record<string, boolean>>({});
  const annotoriousIdToApiId = ref<Record<string, string>>({});
  const fetchQueue = ref<FetchCall[]>([]);
  const processingQueue = ref(false);

  const imageCount = computed(() => annotatedImages.value.length);
  const totalAnnotations = computed(() =>
    annotatedImages.value.reduce((count, img) => count + img.annotations.length, 0),
  );
  const addingNewImage = ref(false);
  const overlapLoading = computed(() =>
    selectedImageUrl.value ? overlapsLoading.value[selectedImageUrl.value] === true : false,
  );
  const selectedImage = computed(() =>
    selectedImageUrl.value
      ? (annotatedImages.value.find((img) => img.imageUrl === selectedImageUrl.value) ?? null)
      : null,
  );

  async function loadAnnotations(annotatorId?: number) {
    const url = annotatorId
      ? `${baseUrl}/annotations/annotated-images/?annotator_id=${annotatorId}`
      : `${baseUrl}/annotations/annotated-images/`;
    try {
      const response = await enqueueFetch(url);
      const images = await response.json();

      annotatedImages.value = images.map((img: AnnotatedImageRead) => ({
        imageId: img.id,
        imageUrl: `${baseUrl}/files/get/${img.image_path}`,
        annotations: img.annotations.map((ann: AnnotationRead) => annotationFromApi(ann)),
        completed: img.completed || false,
        validationStatus: img.validation_status,
      }));

      if (annotatedImages.value.length > 0 && !selectedImageUrl.value) {
        selectedImageUrl.value = annotatedImages.value[annotatedImages.value.length - 1]!.imageUrl;
      }

      annotoriousIdToApiId.value = {};
    } catch (error) {
      console.error('Failed to load annotations:', error);
      const { Notify } = await import('quasar');
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToLoadAnnotations'),
      });
    }
  }

  async function addImage(imageUrl: string) {
    const path = imageUrl.replace(`${baseUrl}/files/get/`, '');
    try {
      const response = await enqueueFetch(`${baseUrl}/annotations/annotated-images/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_path: path }),
      });
      if (!response.ok) {
        if (response.status === 409) {
          return;
        }
        throw new Error('Failed to add image');
      }
      const data = await response.json();

      const newImage: AnnotatedImage = {
        imageId: data.id,
        imageUrl: imageUrl,
        annotations: [],
        completed: false,
      };

      annotatedImages.value.push(newImage);
      if (!selectedImageUrl.value) {
        selectedImageUrl.value = imageUrl;
      }
    } catch (error) {
      console.error('Failed to add image:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToAddImage'),
      });
    }
  }

  async function removeImage(imageUrl: string) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image || !image.imageId) return;

    try {
      annotatedImages.value = annotatedImages.value.filter((img) => img.imageUrl !== imageUrl);
      const response = await enqueueFetch(
        `${baseUrl}/annotations/annotated-images/${image.imageId}`,
        {
          method: 'DELETE',
        },
      );
      if (!response.ok) {
        throw new Error('Failed to remove image');
      }
    } catch (error) {
      console.error('Failed to remove image:', error);
      annotatedImages.value.push(image);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToRemoveImage'),
      });
    }
  }

  function getAnnotationsForImage(imageUrl: string): Annotation[] {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    return image?.annotations ?? [];
  }

  async function addAnnotation(imageUrl: string, annotation: Annotation) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image || !image.imageId) return;

    const apiData = annotationToApi(annotation);
    try {
      const response = await enqueueFetch(`${baseUrl}/annotations/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          annotated_image_id: image.imageId,
          polygon: apiData.polygon,
          damage_level: apiData.damage_level,
        }),
      });
      if (!response.ok) {
        throw new Error('Failed to add annotation');
      }
      const data = await response.json();
      console.log(`Annotation ${data.id} added successfully`);

      image.annotations.push(annotation);
      annotoriousIdToApiId.value[annotation.id] = data.id.toString();

      if (image.completed) {
        Notify.create({
          type: 'warning',
          message: getI18nT()('completionMarkRemoved'),
        });
        await updateImageCompleted(imageUrl, false);
      }

      return annotation;
    } catch (error) {
      console.error('Failed to add annotation:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToAddAnnotation'),
      });
      return annotation;
    }
  }

  async function updateAnnotation(imageUrl: string, annotation: Annotation) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image) return;

    const apiData = annotationToApi(annotation);
    try {
      const response = await enqueueFetch(
        () =>
          `${baseUrl}/annotations/${annotoriousIdToApiId.value[annotation.id] || annotation.id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(apiData),
        },
      );
      if (!response.ok) {
        throw new Error('Failed to update annotation');
      }
      const annotationId = annotoriousIdToApiId.value[annotation.id] || annotation.id;
      console.log(`Annotation ${annotationId} updated successfully`);
      const index = image.annotations.findIndex((a) => a.id === annotation.id);
      if (index !== -1) {
        image.annotations[index] = annotation;
      }

      if (image.completed && apiData.damage_level === 'unset') {
        Notify.create({
          type: 'warning',
          message: getI18nT()('completionMarkRemoved'),
        });
        await updateImageCompleted(imageUrl, false);
      }
    } catch (error) {
      console.error('Failed to update annotation:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToUpdateAnnotation'),
      });
    }
  }

  async function deleteAnnotation(imageUrl: string, annotation: Annotation) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image) return;

    try {
      const response = await enqueueFetch(
        () =>
          `${baseUrl}/annotations/${annotoriousIdToApiId.value[annotation.id] || annotation.id}`,
        {
          method: 'DELETE',
        },
      );
      if (!response.ok) {
        throw new Error('Failed to delete annotation');
      }
      const annotationId = annotoriousIdToApiId.value[annotation.id] || annotation.id;
      console.log(`Annotation ${annotationId} deleted successfully`);
      image.annotations = image.annotations.filter((a) => a.id !== annotation.id);
    } catch (error) {
      console.error('Failed to delete annotation:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToDeleteAnnotation'),
      });
    }
  }

  function setSelectedImageUrl(url: string | null) {
    selectedImageUrl.value = url;
  }

  async function addAnnotationsFromOverlap(imageUrl: string, overlap: Overlap | null) {
    if (!overlap) return;
    if (overlap.overlap_ratio < OVERLAP_RATIO_THRESHOLD) return;

    const sourceAnnotations = getAnnotationsForImage(`${baseUrl}/files/get/${overlap.image_path}`);
    if (sourceAnnotations.length === 0) return;

    const H = overlap.homography_matrix;
    const addAnnotationPromises: Promise<void>[] = [];

    for (const sourceAnnotation of sourceAnnotations) {
      const transformedPoints = sourceAnnotation.target.selector.geometry.points.map(
        (point: Point): Point => {
          const [x, y] = point;
          const x1 = H[0]![0]! * x + H[0]![1]! * y + H[0]![2]!;
          const y1 = H[1]![0]! * x + H[1]![1]! * y + H[1]![2]!;
          const w = H[2]![0]! * x + H[2]![1]! * y + H[2]![2]!;

          return [x1 / w, y1 / w];
        },
      );

      const bounds = {
        minX: Math.min(...transformedPoints.map((p) => p[0])),
        maxX: Math.max(...transformedPoints.map((p) => p[0])),
        minY: Math.min(...transformedPoints.map((p) => p[1])),
        maxY: Math.max(...transformedPoints.map((p) => p[1])),
      };

      if (
        bounds.maxX < 0 ||
        bounds.minX > overlap.resolution[0] ||
        bounds.maxY < 0 ||
        bounds.minY > overlap.resolution[1]
      ) {
        continue;
      }

      const newAnnotation: Annotation = {
        id: sourceAnnotation.id,
        bodies: sourceAnnotation.bodies,
        target: {
          ...sourceAnnotation.target,
          selector: {
            ...sourceAnnotation.target.selector,
            geometry: {
              bounds,
              points: transformedPoints,
            },
          },
        },
      };

      addAnnotationPromises.push(
        addAnnotation(imageUrl, newAnnotation)
          .then(() => {})
          .catch((error) => {
            console.error('Failed to add annotation from overlap:', error);
          }),
      );
    }

    try {
      await Promise.all(addAnnotationPromises);
      const t = getI18nT();
      Notify.create({
        message: t('annotationsCopied', { filename: overlap.image_path.split('/').slice(-1)[0] }),
      });
    } catch (error) {
      console.error('Failed to add annotations from overlap:', error);
    }
  }

  function setUserInfo(newUserInfo: AnnotationData['userInfo']) {
    userInfo.value = newUserInfo;
  }

  function clearAll() {
    userInfo.value = {
      fullName: '',
      email: '',
    };
    annotatedImages.value = [];
  }

  async function updateImageCompleted(imageUrl: string, completed: boolean) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image || !image.imageId) return;

    try {
      const response = await enqueueFetch(
        `${baseUrl}/annotations/annotated-images/${image.imageId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ completed }),
        },
      );
      if (!response.ok) {
        throw new Error('Failed to update image completed status');
      }
      image.completed = completed;
    } catch (error) {
      console.error('Failed to update image completed status:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToUpdateCompleted'),
      });
    }
  }

  async function updateImageValidationStatus(imageUrl: string, status: ValidationStatus) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image || !image.imageId) return;

    const endpoint = status === 'approved' ? 'approve' : 'reject';
    try {
      const response = await enqueueFetch(
        `${baseUrl}/annotations/annotated-images/${image.imageId}/${endpoint}`,
        {
          method: 'POST',
        },
      );
      if (!response.ok) {
        throw new Error('Failed to update image validation status');
      }
      image.validationStatus = status;
    } catch (error) {
      console.error('Failed to update image validation status:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToUpdateValidationStatus'),
      });
    }
  }

  async function processFetchQueue() {
    if (processingQueue.value || fetchQueue.value.length === 0) {
      return;
    }
    processingQueue.value = true;

    while (fetchQueue.value.length > 0) {
      const run = fetchQueue.value[0]!;
      await run();
      fetchQueue.value.shift();
    }

    processingQueue.value = false;
  }

  function enqueueFetch(url: string | (() => string), options?: RequestInit): Promise<Response> {
    return new Promise((resolve, reject) => {
      fetchQueue.value.push(async () => {
        try {
          const resolvedUrl = typeof url === 'function' ? url() : url;
          const response = await authFetch(resolvedUrl, options);
          resolve(response);
        } catch (error) {
          reject(error instanceof Error ? error : new Error(String(error)));
        }
      });
      void processFetchQueue();
    });
  }

  function setNextImageForReview() {
    const currentIndex = annotatedImages.value.findIndex(
      (img) => img.imageUrl === selectedImageUrl.value,
    );
    // Find the next image with pending validation status after the current one
    for (let i = currentIndex + 1; i < annotatedImages.value.length; i++) {
      const img = annotatedImages.value[i]!;
      if (img.validationStatus === 'pending' || !img.validationStatus) {
        selectedImageUrl.value = img.imageUrl;
        return;
      }
    }
    // If no more pending images after current, check from the start
    for (let i = 0; i <= currentIndex; i++) {
      const img = annotatedImages.value[i]!;
      if (img.validationStatus === 'pending' || !img.validationStatus) {
        selectedImageUrl.value = img.imageUrl;
        return;
      }
    }
    // No pending images found
    Notify.create({
      type: 'info',
      message: getI18nT()('noMoreImagesToReview'),
    });
  }

  return {
    userInfo,
    annotatedImages,
    selectedImageUrl,
    overlapsLoading,
    annotoriousIdToApiId,
    fetchQueue,
    processingQueue,
    imageCount,
    totalAnnotations,
    addingNewImage,
    overlapLoading,
    selectedImage,
    loadAnnotations,
    addImage,
    removeImage,
    getAnnotationsForImage,
    addAnnotation,
    updateAnnotation,
    deleteAnnotation,
    setSelectedImageUrl,
    addAnnotationsFromOverlap,
    setUserInfo,
    clearAll,
    updateImageCompleted,
    updateImageValidationStatus,
    processFetchQueue,
    enqueueFetch,
    setNextImageForReview,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAnnotationDataStore, import.meta.hot));
}
