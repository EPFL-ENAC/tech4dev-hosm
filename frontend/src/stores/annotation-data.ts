import { defineStore, acceptHMRUpdate } from 'pinia';
import type { AnnotationData, Annotation, Overlap } from '../models';
import { exportFile } from 'quasar';

export const DAMAGE_LEVELS = 4;

export const DAMAGE_COLORS = [
  // Taken from Paul Tol
  '#bbbbbb',
  '#4477aa',
  '#ccbb44',
  '#ee6677',
];

export const useAnnotationDataStore = defineStore('annotationData', {
  state: (): AnnotationData & { selectedImageUrl: string | null; overlapLoading: boolean } => ({
    userInfo: {
      firstName: '',
      lastName: '',
      email: '',
    },
    annotatedImages: [],
    selectedImageUrl: null,
    overlapLoading: false,
  }),

  getters: {
    imageCount: (state): number => state.annotatedImages.length,
    totalAnnotations: (state): number =>
      state.annotatedImages.reduce((count, img) => count + img.annotations.length, 0),
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
