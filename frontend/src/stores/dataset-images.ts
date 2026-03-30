import { defineStore } from 'pinia';
import { baseUrl } from 'boot/api';

export const useDatasetImagesStore = defineStore('datasetImages', {
  state: () => ({
    imageUrls: [] as string[],
    preloadedImageUrl: null as string | null,
  }),

  actions: {
    async loadImageUrls() {
      try {
        const response = await fetch('/datasets.json');
        const directoryPaths = await response.json();

        const urls: string[] = [];
        for (const dirPath of directoryPaths) {
          const encodedDirPath = dirPath.replaceAll('/', '%2F');
          const listResponse = await fetch(`${baseUrl}/files/list/${encodedDirPath}`);
          const data = await listResponse.json();

          const imageFiles = data.files.filter(
            (file: string) => file.endsWith('.jpg') || file.endsWith('.JPG'),
          );

          const encodedPath = dirPath.replaceAll('/', '%2F');
          const fullUrls = imageFiles.map(
            (file: string) => `${baseUrl}/files/get/${encodedPath}/${file}`,
          );
          urls.push(...fullUrls);
        }

        this.imageUrls = urls;
      } catch (error) {
        console.error('Failed to load dataset images:', error);
      }

      this.preloadImage(this.getRandomImageUrl());
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

    getNextImageUrl(excludeUrls: string[] = []): string | null {
      let nextUrl;

      if (this.preloadedImageUrl && !excludeUrls.includes(this.preloadedImageUrl)) {
        nextUrl = this.preloadedImageUrl;
        excludeUrls.push(nextUrl);
      }

      const newPreloadUrl = this.getRandomImageUrl(excludeUrls);
      if (!newPreloadUrl) {
        return nextUrl ?? null;
      }

      this.preloadImage(newPreloadUrl);
      excludeUrls.push(newPreloadUrl);
      return nextUrl ?? this.getRandomImageUrl(excludeUrls);
    },

    preloadImage(url: string | null): void {
      this.preloadedImageUrl = url;

      if (!url) {
        return;
      }

      setTimeout(() => {
        // const img = new Image();
        // img.src = url;

        fetch(url, {
          method: 'GET',
          mode: 'cors',
          cache: 'default',
          headers: {
            'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
            'Sec-Fetch-Dest': 'image',
          },
        }).catch((error) => {
          console.error('Failed to preload image:', error);
        });
      }, 1000);
    },
  },
});
