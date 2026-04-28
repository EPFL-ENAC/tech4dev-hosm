import { defineStore } from 'pinia';
import { ref, computed, reactive } from 'vue';
import { baseUrl, authFetch } from 'boot/api';
import { Notify } from 'quasar';
import type { UserReadWithStats, PaginatedResponse } from '../models';

// Valid sort fields matching backend VALID_USER_SORT_FIELDS
const VALID_SORT_FIELDS = [
  'full_name',
  'email',
  'role',
  'created_at',
  'last_action_at',
  'annotated_images_count',
  'total_annotations_count',
];

export interface UserPagination {
  page: number;
  pageSize: number;
  sortBy: string;
  descending: boolean;
  total: number;
}

export const useUsersStore = defineStore('users', () => {
  // User data
  const users = ref<UserReadWithStats[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Abort controller for cancelling in-flight requests
  let abortController: AbortController | null = null;

  // Single source of truth for pagination state
  const pagination = reactive<UserPagination>({
    page: 1,
    pageSize: 20,
    sortBy: 'full_name',
    descending: false,
    total: 0,
  });

  // Computed properties
  const isLoading = computed(() => loading.value);
  const totalPages = computed(() => {
    return pagination.total > 0 ? Math.ceil(pagination.total / pagination.pageSize) : 1;
  });

  /**
   * Fetch users from API with current pagination settings
   */
  async function fetchUsers(signal?: AbortSignal) {
    // Cancel any in-flight request before starting a new one
    if (abortController) {
      abortController.abort();
    }
    abortController = new AbortController();
    const combinedSignal = signal || abortController.signal;

    loading.value = true;
    error.value = null;
    try {
      const sortOrder = pagination.descending ? 'desc' : 'asc';
      const params = new URLSearchParams({
        page: String(pagination.page),
        page_size: String(pagination.pageSize),
        sort_by: pagination.sortBy,
        sort_order: sortOrder,
      });
      const response = await authFetch(`${baseUrl}/annotations/users/?${params.toString()}`, {
        signal: combinedSignal,
      });
      const data: PaginatedResponse<UserReadWithStats> = await response.json();
      users.value = data.items;
      pagination.total = data.total;
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Request was cancelled, ignore
        return;
      }
      console.error('Failed to fetch users:', err);
      error.value = err instanceof Error ? err.message : 'Failed to load users';
      Notify.create({
        message: 'Failed to load users. Please try again.',
        color: 'negative',
        position: 'top',
        timeout: 3000,
      });
    } finally {
      loading.value = false;
    }
  }

  /**
   * Update pagination settings and fetch new data
   */
  async function setPagination(newPagination: Partial<UserPagination>) {
    Object.assign(pagination, newPagination);
    await fetchUsers();
  }

  /**
   * Validate sort field against known valid fields
   */
  function isValidSortField(field: string): boolean {
    return VALID_SORT_FIELDS.includes(field);
  }

  /**
   * Toggle sort order for a field or set a new sort field
   */
  async function setSort(field: string, order: 'asc' | 'desc' = 'asc') {
    // Validate sort field before proceeding
    if (!VALID_SORT_FIELDS.includes(field)) {
      console.warn(`Invalid sort field: ${field}. Must be one of: ${VALID_SORT_FIELDS.join(', ')}`);
      Notify.create({
        message: `Invalid sort field. Must be one of: ${VALID_SORT_FIELDS.join(', ')}`,
        color: 'warning',
        position: 'top',
        timeout: 3000,
      });
      return;
    }

    if (pagination.sortBy === field) {
      pagination.descending = pagination.descending ? false : true;
    } else {
      pagination.sortBy = field;
      pagination.descending = order === 'desc';
    }
    pagination.page = 1;
    await fetchUsers();
  }

  return {
    users,
    pagination,
    loading,
    isLoading,
    totalPages,
    error,
    fetchUsers,
    setPagination,
    setSort,
    isValidSortField,
  };
});
