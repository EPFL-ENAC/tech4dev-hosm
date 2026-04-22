import { defineStore, acceptHMRUpdate } from 'pinia';
import { baseUrl, authFetch } from 'boot/api';
import type {
  AnnotatedImage,
  AnnotationData,
  Annotation,
  Overlap,
  Point,
  AnnotatedImageRead,
  AnnotationRead,
} from '../models';
import { Notify } from 'quasar';
import { getI18nT } from 'src/utils/i18n';

export const DAMAGE_LEVELS = 4;

export const DAMAGE_COLORS = [
  // Taken from Paul Tol
  '#bbbbbb',
  '#4477aa',
  '#ccbb44',
  '#ee6677',
];

const OVERLAP_RATIO_THRESHOLD = 0.3;

function annotationToApi(annotation: Annotation): { polygon: number[][]; damage_level: number } {
  const damageBody = annotation.bodies.find((b) => b.purpose === 'damage');
  const damageLevel = damageBody ? parseInt(damageBody.value) : 0;
  const polygon = annotation.target.selector.geometry.points;
  return { polygon, damage_level: damageLevel };
}

function annotationFromApi(apiAnnotation: {
  id: number;
  polygon: number[][];
  damage_level: number;
}): Annotation {
  return {
    id: apiAnnotation.id.toString(),
    bodies: [{ purpose: 'damage', value: apiAnnotation.damage_level.toString() }],
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

export const useAnnotationDataStore = defineStore('annotationData', {
  state: (): AnnotationData & {
    selectedImageUrl: string | null;
    overlapsLoading: Record<string, boolean>;
    annotoriousIdToApiId: Record<string, string>;
  } => ({
    userInfo: {
      fullName: '',
      email: '',
    },
    annotatedImages: [],
    selectedImageUrl: null,
    overlapsLoading: {},
    annotoriousIdToApiId: {},
  }),

  getters: {
    imageCount: (state): number => state.annotatedImages.length,
    totalAnnotations: (state): number =>
      state.annotatedImages.reduce((count, img) => count + img.annotations.length, 0),
    overlapLoading: (state): boolean =>
      state.selectedImageUrl ? state.overlapsLoading[state.selectedImageUrl] === true : false,
    selectedImage: (state): AnnotatedImage | null =>
      state.selectedImageUrl
        ? (state.annotatedImages.find((img) => img.imageUrl === state.selectedImageUrl) ?? null)
        : null,
  },

  actions: {
    async loadAnnotations() {
      try {
        const response = await authFetch(`${baseUrl}/annotations/annotated-images/`);
        const images = await response.json();

        this.annotatedImages = images.map((img: AnnotatedImageRead) => ({
          imageId: img.id,
          imageUrl: `${baseUrl}/files/get/${img.image_path}`,
          annotations: img.annotations.map((ann: AnnotationRead) => annotationFromApi(ann)),
          completed: img.completed || false,
        }));

        if (this.annotatedImages.length > 0 && !this.selectedImageUrl) {
          this.selectedImageUrl = this.annotatedImages[this.annotatedImages.length - 1]!.imageUrl;
        }

        this.annotoriousIdToApiId = {};
      } catch (error) {
        console.error('Failed to load annotations:', error);
        const { Notify } = await import('quasar');
        Notify.create({
          type: 'negative',
          message: getI18nT()('failedToLoadAnnotations'),
        });
      }
    },

    async addImage(imageUrl: string) {
      const path = imageUrl.replace(`${baseUrl}/files/get/`, '');
      try {
        const response = await authFetch(`${baseUrl}/annotations/annotated-images/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_path: path }),
        });
        if (!response.ok) {
          throw new Error('Failed to add image');
        }
        const data = await response.json();

        const newImage: AnnotatedImage = {
          imageId: data.id,
          imageUrl: imageUrl,
          annotations: [],
          completed: false,
        };

        this.annotatedImages.push(newImage);
        if (!this.selectedImageUrl) {
          this.selectedImageUrl = imageUrl;
          this.annotoriousIdToApiId = {};
        }
      } catch (error) {
        console.error('Failed to add image:', error);
        Notify.create({
          type: 'negative',
          message: getI18nT()('failedToAddImage'),
        });
      }
    },

    async removeImage(imageUrl: string) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (!image || !image.imageId) return;

      try {
        const response = await authFetch(
          `${baseUrl}/annotations/annotated-images/${image.imageId}`,
          {
            method: 'DELETE',
          },
        );
        if (!response.ok) {
          throw new Error('Failed to remove image');
        }
        this.annotatedImages = this.annotatedImages.filter((img) => img.imageUrl !== imageUrl);
      } catch (error) {
        console.error('Failed to remove image:', error);
        Notify.create({
          type: 'negative',
          message: getI18nT()('failedToRemoveImage'),
        });
      }
    },

    getAnnotationsForImage(imageUrl: string): Annotation[] {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      return image?.annotations ?? [];
    },

    async addAnnotation(imageUrl: string, annotation: Annotation) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (!image || !image.imageId) return;

      try {
        const apiData = annotationToApi(annotation);
        const response = await authFetch(`${baseUrl}/annotations/`, {
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

        const newAnnotation: Annotation = {
          ...annotation,
          id: data.id.toString(),
        };
        image.annotations.push(newAnnotation);
        this.annotoriousIdToApiId[annotation.id] = newAnnotation.id;

        return newAnnotation;
      } catch (error) {
        console.error('Failed to add annotation:', error);
        Notify.create({
          type: 'negative',
          message: getI18nT()('failedToAddAnnotation'),
        });
        return annotation;
      }
    },

    async updateAnnotation(imageUrl: string, annotation: Annotation) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (!image) return;

      try {
        const apiData = annotationToApi(annotation);
        const annotationId = this.annotoriousIdToApiId[annotation.id] || annotation.id;
        const response = await authFetch(`${baseUrl}/annotations/${annotationId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(apiData),
        });
        if (!response.ok) {
          throw new Error('Failed to update annotation');
        }
        const index = image.annotations.findIndex((a) => a.id === annotationId);
        if (index !== -1) {
          image.annotations[index] = annotation;
        }
      } catch (error) {
        console.error('Failed to update annotation:', error);
        Notify.create({
          type: 'negative',
          message: getI18nT()('failedToUpdateAnnotation'),
        });
      }
    },

    async deleteAnnotation(imageUrl: string, annotation: Annotation) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (!image) return;

      try {
        const response = await authFetch(`${baseUrl}/annotations/${annotation.id}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error('Failed to delete annotation');
        }
        image.annotations = image.annotations.filter((a) => a.id !== annotation.id);
      } catch (error) {
        console.error('Failed to delete annotation:', error);
        Notify.create({
          type: 'negative',
          message: getI18nT()('failedToDeleteAnnotation'),
        });
      }
    },

    setSelectedImageUrl(url: string | null) {
      this.selectedImageUrl = url;
      this.annotoriousIdToApiId = {};
    },

    async addAnnotationsFromOverlap(imageUrl: string, overlap: Overlap | null) {
      if (!overlap) return;
      // console.log(
      //   `Detected overlap between ${imageUrl} and ${overlap.image_path} with ratio ${overlap.overlap_ratio}`,
      // );
      if (overlap.overlap_ratio < OVERLAP_RATIO_THRESHOLD) return;

      const sourceAnnotations = this.getAnnotationsForImage(
        `${baseUrl}/files/get/${overlap.image_path}`,
      );
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
          this.addAnnotation(imageUrl, newAnnotation)
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
    },

    selectPrevious(): void {
      if (this.annotatedImages.length === 0) return;

      const currentIndex = this.annotatedImages.findIndex(
        (img) => img.imageUrl === this.selectedImageUrl,
      );

      if (currentIndex === -1 || !this.selectedImageUrl) {
        this.selectedImageUrl = this.annotatedImages[0]?.imageUrl ?? null;
        this.annotoriousIdToApiId = {};
        return;
      }

      const prevIndex = currentIndex > 0 ? currentIndex - 1 : this.annotatedImages.length - 1;
      this.selectedImageUrl = this.annotatedImages[prevIndex]?.imageUrl ?? null;
      this.annotoriousIdToApiId = {};
    },

    selectNext(): void {
      if (this.annotatedImages.length === 0) return;

      const currentIndex = this.annotatedImages.findIndex(
        (img) => img.imageUrl === this.selectedImageUrl,
      );

      if (currentIndex === -1 || !this.selectedImageUrl) {
        this.selectedImageUrl = this.annotatedImages[0]?.imageUrl ?? null;
        this.annotoriousIdToApiId = {};
        return;
      }

      const nextIndex = currentIndex < this.annotatedImages.length - 1 ? currentIndex + 1 : 0;
      this.selectedImageUrl = this.annotatedImages[nextIndex]?.imageUrl ?? null;
      this.annotoriousIdToApiId = {};
    },

    setUserInfo(userInfo: AnnotationData['userInfo']) {
      this.userInfo = userInfo;
    },

    clearAll() {
      this.userInfo = {
        fullName: '',
        email: '',
      };
      this.annotatedImages = [];
    },

    async updateImageCompleted(imageUrl: string, completed: boolean) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (!image || !image.imageId) return;

      try {
        const response = await authFetch(
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
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAnnotationDataStore, import.meta.hot));
}
