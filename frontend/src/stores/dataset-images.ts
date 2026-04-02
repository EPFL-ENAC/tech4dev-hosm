import { defineStore } from 'pinia';
import { baseUrl } from 'boot/api';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { type Overlap } from 'src/models';

const annotationStore = useAnnotationDataStore();

export const useDatasetImagesStore = defineStore('datasetImages', {
  state: () => ({
    imageUrls: [] as string[],
    preloadedImageUrl: null as string | null,
    preloadedOverlap: null as Promise<Overlap | null> | null,
  }),

  actions: {
    async loadImageUrls() {
      try {
        const response = await fetch('/datasets.json');
        const directoryPaths = await response.json();

        const urls: string[] = [];
        for (const dirPath of directoryPaths) {
          const listResponse = await fetch(`${baseUrl}/files/list/${dirPath}`);
          const data = await listResponse.json();

          const imageFiles = data.files.filter(
            (file: string) => file.endsWith('.jpg') || file.endsWith('.JPG'),
          );

          const fullUrls = imageFiles.map(
            (file: string) => `${baseUrl}/files/get/${dirPath}/${file}`,
          );
          urls.push(...fullUrls);
        }

        this.imageUrls = urls;
        // this.imageUrls = urls.filter((url) => url.includes('DJI_004')); // For testing overlaps
      } catch (error) {
        console.error('Failed to load dataset images:', error);
      }

      this.preloadNextImage();
    },

    getRandomImageUrl(excludeUrls: string[] = []): string | null {
      if (this.imageUrls.length === 0) {
        return null;
      }

      const availableUrls = this.imageUrls.filter((url) => !excludeUrls.includes(url));

      if (availableUrls.length === 0) {
        return null;
      }

      const randomIndex = Math.floor(Math.random() * availableUrls.length);
      return availableUrls[randomIndex] ?? null;
    },

    getAllUrls(): string[] {
      return [...this.imageUrls];
    },

    getNextImageInfo(): [string | null, Promise<Overlap | null> | null] {
      const url = this.preloadedImageUrl;
      const overlap = this.preloadedOverlap;
      this.preloadNextImage(url);
      return [url, overlap];
    },

    preloadNextImage(excluded_url: string | null = null): void {
      const annotatedUrls = annotationStore.annotatedImages.map((img) => img.imageUrl);
      if (excluded_url) {
        annotatedUrls.push(excluded_url);
      }
      const nextUrl = this.getRandomImageUrl(annotatedUrls);
      this.preloadedImageUrl = nextUrl;

      if (!nextUrl) {
        return;
      }

      const nextImageName = nextUrl.split('/').slice(-1)[0];
      console.log('Preloading image:', nextImageName);

      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.src = nextUrl;

      // Preload overlap info
      const imagePath = nextUrl.replaceAll(`${baseUrl}/files/get/`, '');
      const imageDir = imagePath.split('/').slice(0, -1).join('/');
      const otherPaths = annotatedUrls.map((url) => url.replaceAll(`${baseUrl}/files/get/`, ''));
      otherPaths.filter((path) => path.startsWith(imageDir));
      const otherNames = otherPaths.map((path) => path.split('/').slice(-1)[0]);

      let resolveOverlap: (overlap: Overlap) => void;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let rejectOverlap: (error: any) => void;

      this.preloadedOverlap = new Promise((resolve, reject) => {
        resolveOverlap = resolve;
        rejectOverlap = reject;
      });

      fetch(`${baseUrl}/images/best-overlap/${imagePath}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(otherNames),
      })
        .then((response) => response.json())
        .then((overlap: Overlap) => {
          console.log('Done loading overlap for', nextImageName);
          resolveOverlap(overlap);
        })
        .catch((error) => {
          console.error('Failed to load overlap for', nextImageName, error);
          rejectOverlap(error);
        });
    },
  },
});
