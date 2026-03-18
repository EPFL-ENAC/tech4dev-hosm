import { defineStore } from 'pinia';

export const useDatasetImagesStore = defineStore('datasetImages', {
  state: () => ({
    imageUrls: [] as string[],
  }),

  actions: {
    async loadImageUrls() {
      try {
        const response = await fetch('/datasets.json');
        const data = await response.json();

        const urls: string[] = [];
        for (const dataset in data) {
          if (data[dataset].imageUrls) {
            urls.push(...data[dataset].imageUrls);
          }
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
      
      const availableUrls = this.imageUrls.filter(
        (url) => !excludeUrls.includes(url)
      );
      
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
