import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { baseUrl, authFetch } from 'boot/api';
import { Notify } from 'quasar';
import type { AnnotatedImagesCounts } from '../models';

export const useAdminStatsStore = defineStore('adminStats', () => {
  const totalImagesCount = ref<number>(0);
  const annotatedImagesCounts = ref<AnnotatedImagesCounts | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isLoading = computed(() => loading.value);

  async function fetchStats(signal?: AbortSignal) {
    loading.value = true;
    error.value = null;

    try {
      const fetchOptions: RequestInit = signal ? { signal } : {};
      const [imagesResponse, annotationsResponse] = await Promise.all([
        authFetch(`${baseUrl}/images/total-images-count`, fetchOptions),
        authFetch(`${baseUrl}/annotations/annotated-images-counts`, fetchOptions),
      ]);

      if (!imagesResponse.ok) {
        throw new Error(`Failed to fetch images count: ${imagesResponse.statusText}`);
      }
      if (!annotationsResponse.ok) {
        throw new Error(`Failed to fetch annotations counts: ${annotationsResponse.statusText}`);
      }

      totalImagesCount.value = (await imagesResponse.json()) as number;
      annotatedImagesCounts.value = (await annotationsResponse.json()) as AnnotatedImagesCounts;
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }
      console.error('Failed to fetch admin stats:', err);
      error.value = err instanceof Error ? err.message : 'Failed to load statistics';
      Notify.create({
        message: 'Failed to load statistics. Please try again.',
        color: 'negative',
        position: 'top',
        timeout: 3000,
      });
    } finally {
      loading.value = false;
    }
  }

  return {
    totalImagesCount,
    annotatedImagesCounts,
    loading,
    isLoading,
    error,
    fetchStats,
  };
});
