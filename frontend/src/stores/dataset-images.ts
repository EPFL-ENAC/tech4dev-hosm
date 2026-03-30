import { defineStore } from 'pinia';
import { baseUrl } from 'boot/api';

export const useDatasetImagesStore = defineStore('datasetImages', {
  state: () => ({
    imageUrls: [] as string[],
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
  },
});
