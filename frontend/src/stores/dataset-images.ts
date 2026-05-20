import { defineStore } from 'pinia';
import { ref } from 'vue';
import { baseUrl, authFetch } from 'boot/api';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { type Overlap, type ImageGPSLocation } from 'src/models';

export const useDatasetImagesStore = defineStore('datasetImages', () => {
  const annotationStore = useAnnotationDataStore();
  const preloadedImageUrl = ref<string | null>(null);
  const preloadedOverlap = ref<Promise<Overlap | null> | null>(null);

  async function getRandomImageUrl(excludedUrls: string[] = []): Promise<string | null> {
    const excludedPaths = excludedUrls.map((url) => url.replaceAll(`${baseUrl}/files/get/`, ''));

    try {
      const response = await authFetch(`${baseUrl}/images/random`, {
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
  }

  function getNextImageInfo(): [string | null, Promise<Overlap | null> | null] {
    const url = preloadedImageUrl.value;
    const overlap = preloadedOverlap.value;
    preloadNextImage(url);
    return [url, overlap];
  }

  function preloadNextImage(excluded_url: string | null = null): void {
    const annotatedUrls = annotationStore.annotatedImages.map((img) => img.imageUrl);
    if (excluded_url) {
      annotatedUrls.push(excluded_url);
    }
    getRandomImageUrl(annotatedUrls)
      .then((nextUrl) => {
        preloadedImageUrl.value = nextUrl;

        if (!nextUrl) {
          return;
        }

        const nextImageName = nextUrl.split('/').slice(-1)[0];
        const imagePath = nextUrl.replaceAll(`${baseUrl}/files/get/`, '');
        const imageDir = imagePath.split('/').slice(0, -1).join('/');
        let otherPaths = annotatedUrls.map((url) => url.replaceAll(`${baseUrl}/files/get/`, ''));
        otherPaths = otherPaths.filter((path) => path.startsWith(imageDir));
        const otherNames = otherPaths.map((path) => path.split('/').slice(-1)[0]);

        let resolveOverlap: (overlap: Overlap) => void;
        let rejectOverlap: (error: unknown) => void;

        preloadedOverlap.value = new Promise((resolve, reject) => {
          resolveOverlap = resolve;
          rejectOverlap = reject;
        });

        authFetch(`${baseUrl}/images/best-overlap/${imagePath}`, {
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
        preloadedImageUrl.value = null;
        preloadedOverlap.value = null;
      });
  }

  async function getImageLocation(imageUrl: string): Promise<ImageGPSLocation> {
    const imagePath = imageUrl.replaceAll(`${baseUrl}/files/get/`, '');
    const response = await authFetch(`${baseUrl}/images/location/${imagePath}`);
    return response.json() as Promise<ImageGPSLocation>;
  }

  return {
    preloadedImageUrl,
    preloadedOverlap,
    getRandomImageUrl,
    getNextImageInfo,
    preloadNextImage,
    getImageLocation,
  };
});
