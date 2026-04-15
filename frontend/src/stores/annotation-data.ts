import { defineStore, acceptHMRUpdate } from 'pinia';
import { baseUrl } from 'boot/api';
import type { AnnotatedImage, AnnotationData, Annotation, Overlap, Point } from '../models';
import { exportFile, Notify } from 'quasar';

const getI18nT = () => {
  if (typeof window !== 'undefined') {
    const win = window as unknown as {
      i18nGlobal?: { t: (key: string, params: Record<string, unknown>) => string };
    };
    if (win.i18nGlobal) {
      return win.i18nGlobal.t;
    }
  }
  return (key: string) => key;
};

export const DAMAGE_LEVELS = 4;

export const DAMAGE_COLORS = [
  // Taken from Paul Tol
  '#bbbbbb',
  '#4477aa',
  '#ccbb44',
  '#ee6677',
];

const OVERLAP_RATIO_THRESHOLD = 0.3;

export const useAnnotationDataStore = defineStore('annotationData', {
  state: (): AnnotationData & {
    selectedImageUrl: string | null;
    overlapsLoading: Record<string, boolean>;
  } => ({
    userInfo: {
      firstName: '',
      lastName: '',
      email: '',
    },
    annotatedImages: [],
    selectedImageUrl: null,
    overlapsLoading: {},
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
    getAnnotationsForImage(imageUrl: string): Annotation[] {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      return image?.annotations ?? [];
    },

    addAnnotation(imageUrl: string, annotation: Annotation) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (image) {
        const existingIndex = image.annotations.findIndex((a) => a.id === annotation.id);
        if (existingIndex !== -1) {
          image.annotations[existingIndex] = annotation;
        } else {
          image.annotations.push(annotation);
        }
      }
    },

    updateAnnotation(imageUrl: string, annotation: Annotation) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (image) {
        const index = image.annotations.findIndex((a) => a.id === annotation.id);
        if (index !== -1) {
          image.annotations[index] = annotation;
        }
      }
    },

    deleteAnnotation(imageUrl: string, annotation: Annotation) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (image) {
        image.annotations = image.annotations.filter((a) => a.id !== annotation.id);
      }
    },

    setSelectedImageUrl(url: string | null) {
      this.selectedImageUrl = url;
    },

    addAnnotationsFromOverlap(imageUrl: string, overlap: Overlap | null) {
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

        this.addAnnotation(imageUrl, newAnnotation);
      }

      const t = getI18nT();
      Notify.create({
        message: t('annotationsCopied', { filename: overlap.image_path.split('/').slice(-1)[0] }),
      });
    },

    selectPrevious(): void {
      if (this.annotatedImages.length === 0) return;

      const currentIndex = this.annotatedImages.findIndex(
        (img) => img.imageUrl === this.selectedImageUrl,
      );

      if (currentIndex === -1 || !this.selectedImageUrl) {
        this.selectedImageUrl = this.annotatedImages[0]?.imageUrl ?? null;
        return;
      }

      const prevIndex = currentIndex > 0 ? currentIndex - 1 : this.annotatedImages.length - 1;
      this.selectedImageUrl = this.annotatedImages[prevIndex]?.imageUrl ?? null;
    },

    selectNext(): void {
      if (this.annotatedImages.length === 0) return;

      const currentIndex = this.annotatedImages.findIndex(
        (img) => img.imageUrl === this.selectedImageUrl,
      );

      if (currentIndex === -1 || !this.selectedImageUrl) {
        this.selectedImageUrl = this.annotatedImages[0]?.imageUrl ?? null;
        return;
      }

      const nextIndex = currentIndex < this.annotatedImages.length - 1 ? currentIndex + 1 : 0;
      this.selectedImageUrl = this.annotatedImages[nextIndex]?.imageUrl ?? null;
    },

    setUserInfo(userInfo: AnnotationData['userInfo']) {
      this.userInfo = userInfo;
    },

    addImage(
      imageUrl: string,
      annotations: AnnotationData['annotatedImages'][0]['annotations'] = [],
    ) {
      const exists = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (!exists) {
        this.annotatedImages.push({ imageUrl, annotations });
        if (!this.selectedImageUrl) {
          this.selectedImageUrl = imageUrl;
        }
      }
    },

    removeImage(imageUrl: string) {
      this.annotatedImages = this.annotatedImages.filter((img) => img.imageUrl !== imageUrl);
    },

    clearAll() {
      this.userInfo = {
        firstName: '',
        lastName: '',
        email: '',
      };
      this.annotatedImages = [];
    },

    exportData() {
      const data = {
        userInfo: this.userInfo,
        annotatedImages: this.annotatedImages,
      };
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `hosm_annotations_${timestamp}.json`;
      exportFile(filename, JSON.stringify(data, null, 2), {
        mimeType: 'application/json',
      });
    },

    importData(file: File) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const data = JSON.parse(event.target?.result as string);
          if (data.userInfo && data.annotatedImages) {
            this.userInfo = data.userInfo;
            this.annotatedImages = data.annotatedImages;
          }
        } catch (error) {
          console.error('Failed to import annotations:', error);
        }
      };
      reader.readAsText(file);
    },
  },

  persist: {
    key: 'annotation-data',
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAnnotationDataStore, import.meta.hot));
}
