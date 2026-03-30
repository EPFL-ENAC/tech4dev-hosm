import { defineStore, acceptHMRUpdate } from 'pinia';
import { type AnnotationData, type Annotation, type Point } from '../models';

const STORAGE_KEY = 'annotation-data';

interface W3CPointSelector {
  type: 'PointSelector';
  x: number;
  y: number;
}

interface W3CFragmentSelector {
  type: 'FragmentSelector';
  value: string;
  conformsTo: string;
}

interface W3CAnnotationBody {
  type: 'TextualBody';
  value: string;
  format: 'text/plain';
  purpose: 'tagging';
}

interface W3CAnnotationTarget {
  source: string;
  selector: W3CPointSelector[] | W3CFragmentSelector;
}

interface W3CAnnotation {
  id: string;
  type: 'Annotation';
  body: W3CAnnotationBody | W3CAnnotationBody[];
  target: W3CAnnotationTarget | string;
}

function generateAnnotationId(): string {
  return `anno_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

function polygonToW3CSelector(points: Point[]): W3CFragmentSelector {
  const pointsStr = points.map((p) => `${Math.round(p.x)},${Math.round(p.y)}`).join(' ');
  return {
    type: 'FragmentSelector',
    value: `polygon ${pointsStr}`,
    conformsTo: 'http://www.w3.org/TR/media-frags/',
  };
}

function w3CSelectorToPolygon(selector: W3CFragmentSelector | W3CPointSelector[]): Point[] {
  if (Array.isArray(selector)) {
    return selector.map((s) => ({ x: s.x, y: s.y }));
  }

  const match = selector.value?.match(/polygon\s+(.+)/);
  if (!match || !match[1]) {
    return [];
  }

  const pointsStr = match[1];
  return pointsStr
    .trim()
    .split(/\s+/)
    .map((pointStr) => {
      const [xStr, yStr] = pointStr.split(',');
      const x = Number(xStr);
      const y = Number(yStr);
      return { x, y };
    })
    .filter((p) => !isNaN(p.x) && !isNaN(p.y));
}

function appAnnotationToW3C(annotation: Annotation, imageUrl: string): W3CAnnotation {
  return {
    id: generateAnnotationId(),
    type: 'Annotation',
    body: {
      type: 'TextualBody',
      value: JSON.stringify({ damageLevel: annotation.damageLevel }),
      format: 'text/plain',
      purpose: 'tagging',
    },
    target: {
      source: imageUrl,
      selector: polygonToW3CSelector(annotation.polygon.points),
    },
  };
}

function w3CToAppAnnotation(annotation: W3CAnnotation): Annotation | null {
  let points: Point[] = [];
  let damageLevel = 0;

  if (typeof annotation.target === 'string') {
    return null;
  }

  if (Array.isArray(annotation.target.selector)) {
    points = annotation.target.selector.map((s) => ({ x: s.x, y: s.y }));
  } else if (annotation.target.selector.type === 'FragmentSelector') {
    points = w3CSelectorToPolygon(annotation.target.selector);
  }

  if (Array.isArray(annotation.body)) {
    const body = annotation.body.find((b) => b.purpose === 'tagging');
    if (body && typeof body.value === 'string') {
      try {
        damageLevel = JSON.parse(body.value).damageLevel || 0;
      } catch {
        damageLevel = 0;
      }
    }
  } else if (typeof annotation.body.value === 'string') {
    try {
      damageLevel = JSON.parse(annotation.body.value).damageLevel || 0;
    } catch {
      damageLevel = 0;
    }
  }

  return {
    polygon: { points },
    damageLevel: damageLevel as 0 | 1 | 2 | 3,
  };
}

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
    getW3CAnnotationsForImage(imageUrl: string): W3CAnnotation[] {
      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (!image || image.annotations.length === 0) {
        return [];
      }
      return image.annotations.map((anno) => appAnnotationToW3C(anno, imageUrl));
    },

    addW3CAnnotation(imageUrl: string, w3cAnnotation: W3CAnnotation) {
      const appAnnotation = w3CToAppAnnotation(w3cAnnotation);
      if (appAnnotation) {
        this.addAnnotation(imageUrl, appAnnotation);
      }
    },

    updateW3CAnnotation(imageUrl: string, w3cAnnotation: W3CAnnotation) {
      const appAnnotation = w3CToAppAnnotation(w3cAnnotation);
      if (!appAnnotation) return;

      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (!image) return;

      const existingAnno = image.annotations.find((anno) => {
        return (
          JSON.stringify(anno.polygon.points) === JSON.stringify(appAnnotation.polygon.points) &&
          anno.damageLevel === appAnnotation.damageLevel
        );
      });

      if (existingAnno) {
        const index = image.annotations.indexOf(existingAnno);
        this.updateAnnotation(imageUrl, index, appAnnotation);
      }
    },

    deleteW3CAnnotation(imageUrl: string, w3cAnnotation: W3CAnnotation) {
      const appAnnotation = w3CToAppAnnotation(w3cAnnotation);
      if (!appAnnotation) return;

      const image = this.annotatedImages.find((img) => img.imageUrl === imageUrl);
      if (!image) return;

      const index = image.annotations.findIndex((anno) => {
        return (
          JSON.stringify(anno.polygon.points) === JSON.stringify(appAnnotation.polygon.points) &&
          anno.damageLevel === appAnnotation.damageLevel
        );
      });

      if (index !== -1) {
        this.removeAnnotation(imageUrl, index);
      }
    },

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
