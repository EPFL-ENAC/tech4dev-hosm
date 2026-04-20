import { defineStore } from 'pinia';
import { baseUrl } from 'boot/api';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { type Overlap, type ImageGPSLocation } from 'src/models';

const annotationStore = useAnnotationDataStore();

export const useDatasetImagesStore = defineStore('datasetImages', {
  state: () => ({
    preloadedImageUrl: null as string | null,
    preloadedOverlap: null as Promise<Overlap | null> | null,
  }),

  actions: {
    async getRandomImageUrl(excludedUrls: string[] = []): Promise<string | null> {
      const excludedPaths = excludedUrls.map((url) => url.replaceAll(`${baseUrl}/files/get/`, ''));

      try {
        const response = await fetch(`${baseUrl}/images/random`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(excludedPaths),
        });
        const path = await response.json();
        return path ? `${baseUrl}/files/get/${path}` : null;
      } catch (error) {
        console.error('Failed to fetch random image:', error);
        return null;
      }
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
      this.getRandomImageUrl(annotatedUrls)
        .then((nextUrl) => {
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
          const otherPaths = annotatedUrls.map((url) =>
            url.replaceAll(`${baseUrl}/files/get/`, ''),
          );
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
              console.log('Done fetching overlap for', nextImageName);
              resolveOverlap(overlap);
            })
            .catch((error) => {
              console.error('Failed to load overlap for', nextImageName, error);
              rejectOverlap(error);
            });
        })
        .catch((error) => {
          console.error('Failed to preload next image:', error);
          this.preloadedImageUrl = null;
          this.preloadedOverlap = null;
        });
    },

    async getImageLocation(imageUrl: string): Promise<ImageGPSLocation> {
      const imagePath = imageUrl.replaceAll(`${baseUrl}/files/get/`, '');
      const response = await fetch(`${baseUrl}/images/location/${imagePath}`);
      return response.json() as Promise<ImageGPSLocation>;
    },
  },
});
