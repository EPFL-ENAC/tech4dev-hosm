import { defineStore, acceptHMRUpdate } from 'pinia';
import { type AnnotationData } from '../models';

const STORAGE_KEY = 'annotation-data';

const getInitialState = (): AnnotationData => ({
  userInfo: {
    firstName: '',
    lastName: '',
    email: '',
  },
  annotatedImages: [],
});

export const useAnnotationDataStore = defineStore('annotationData', {
  state: (): AnnotationData & { selectedImageUrl: string | null } => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.error('Failed to load annotation data from localStorage:', e);
    }
    return { ...getInitialState(), selectedImageUrl: null };
  },

  getters: {
    imageCount: (state): number => state.annotatedImages.length,
    totalAnnotations: (state): number =>
      state.annotatedImages.reduce((count, img) => count + img.annotations.length, 0),
  },

  actions: {
    setSelectedImageUrl(url: string | null) {
      this.selectedImageUrl = url;
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

    addAnnotation(
      imageUrl: string,
      annotation: AnnotationData['annotatedImages'][0]['annotations'][0],
    ) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (image) {
        image.annotations.push(annotation);
      }
    },

    updateAnnotation(
      imageUrl: string,
      annotationIndex: number,
      annotation: AnnotationData['annotatedImages'][0]['annotations'][0],
    ) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (image && image.annotations[annotationIndex]) {
        image.annotations[annotationIndex] = annotation;
      }
    },

    removeAnnotation(imageUrl: string, annotationIndex: number) {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (image && image.annotations[annotationIndex]) {
        image.annotations.splice(annotationIndex, 1);
      }
    },

    clearAll() {
      this.userInfo = getInitialState().userInfo;
      this.annotatedImages = [];
    },
  },

  persist: {
    key: STORAGE_KEY,
    storage: localStorage,
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAnnotationDataStore, import.meta.hot));
}
