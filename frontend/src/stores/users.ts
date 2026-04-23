import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { baseUrl, authFetch } from 'boot/api';
import type { UserReadWithStats, PaginatedResponse } from '../models';

export const useUsersStore = defineStore('users', () => {
  const users = ref<UserReadWithStats[]>([]);
  const currentPage = ref(1);
  const pageSize = ref(20);
  const totalUsers = ref(0);
  const totalPages = ref(0);
  const sortBy = ref('full_name');
  const sortOrder = ref('asc');
  const loading = ref(false);

  const isLoading = computed(() => loading.value);

  async function fetchUsers(page: number = 1) {
    loading.value = true;
    try {
      const response = await authFetch(
        `${baseUrl}/annotations/users/?page=${page}&page_size=${pageSize.value}&sort_by=${sortBy.value}&sort_order=${sortOrder.value}`,
      );
      const data: PaginatedResponse<UserReadWithStats> = await response.json();
      users.value = data.items;
      currentPage.value = data.page;
      totalUsers.value = data.total;
      totalPages.value = data.total_pages;
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      loading.value = false;
    }
  }

  async function setSort(newSortBy: string, newSortOrder: string) {
    if (sortBy.value === newSortBy) {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy.value = newSortBy;
      sortOrder.value = newSortOrder;
    }
    currentPage.value = 1;
    await fetchUsers(1);
  }

  function setSortWithoutFetch(newSortBy: string, newSortOrder: string) {
    sortBy.value = newSortBy;
    sortOrder.value = newSortOrder;
  }

  async function setPage(page: number) {
    currentPage.value = page;
    await fetchUsers(page);
  }

  return {
    users,
    currentPage,
    pageSize,
    totalUsers,
    totalPages,
    sortBy,
    sortOrder,
    loading,
    isLoading,
    fetchUsers,
    setSort,
    setPage,
    setSortWithoutFetch,
  };
});
