<template>
  <q-page class="review-page">
    <div class="q-pa-md">
      <div class="text-h5 q-mb-md">{{ t('usersTableTitle') }}</div>

      <q-table
        :rows="usersStore.users"
        :columns="columns"
        :loading="usersStore.loading"
        :pagination="pagination"
        :rows-per-page-options="[20, 50, 100]"
        row-key="id"
        flat
        bordered
        @request="onRequest"
      >
        <template #body-cell-role="props">
          <q-td :props="props">
            <q-badge :color="props.row.is_reviewer ? 'primary' : 'grey-7'">
              {{ props.row.is_reviewer ? t('roleReviewer') : t('roleAnnotator') }}
            </q-badge>
          </q-td>
        </template>

        <template #body-cell-created_at="props">
          <q-td :props="props">
            {{ formatDate(props.row.created_at) }}
          </q-td>
        </template>
      </q-table>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { onMounted, ref } from 'vue';
import { useUsersStore } from 'stores/users';
import type { UserReadWithStats } from '../models';

interface PaginationSettings {
  rowsPerPage: number;
  page: number;
  sortBy?: string;
  descending?: boolean;
  rowsPerPageOptions?: number[];
}

interface TableColumn {
  name: string;
  label: string;
  field: string | ((row: UserReadWithStats) => string | number | boolean);
  align?: 'left' | 'right' | 'center';
  sortable?: boolean;
}

const { t, locale } = useI18n();
const usersStore = useUsersStore();

const pagination = ref({
  page: 1,
  rowsPerPage: 20,
  rowsNumber: 0,
  sortBy: 'full_name',
  descending: false,
});

let requestPending = false;

onMounted(async () => {
  await usersStore.fetchUsers(1);
  pagination.value.rowsNumber = usersStore.totalUsers;
});

async function onRequest(props: { pagination: PaginationSettings }) {
  if (requestPending) return;
  
  requestPending = true;
  
  try {
    const { page, rowsPerPage, sortBy, descending } = props.pagination;

    pagination.value.page = page;
    pagination.value.rowsPerPage = rowsPerPage;
    pagination.value.sortBy = sortBy || 'full_name';
    pagination.value.descending = descending ?? false;

    usersStore.pageSize = rowsPerPage;

    const sortOrder = descending ? 'desc' : 'asc';
    const apiSortBy = mapSortField(sortBy || 'full_name');
    
    usersStore.setSortWithoutFetch(apiSortBy, sortOrder);
    await usersStore.fetchUsers(page);
    pagination.value.rowsNumber = usersStore.totalUsers;
  } finally {
    requestPending = false;
  }
}

function mapSortField(field: string): string {
  const fieldMap: Record<string, string> = {
    full_name: 'full_name',
    email: 'email',
    role: 'is_reviewer',
    created_at: 'created_at',
    annotated_images_count: 'annotated_images_count',
    total_annotations_count: 'total_annotations_count',
  };
  return fieldMap[field] || 'full_name';
}

const columns: TableColumn[] = [
  {
    name: 'full_name',
    label: t('userName'),
    field: 'full_name',
    align: 'left',
    sortable: true,
  },
  {
    name: 'email',
    label: t('userEmail'),
    field: 'email',
    align: 'left',
    sortable: true,
  },
  {
    name: 'role',
    label: t('userRole'),
    field: 'is_reviewer',
    align: 'center',
    sortable: true,
  },
  {
    name: 'created_at',
    label: t('userAccountCreated'),
    field: 'created_at',
    align: 'left',
    sortable: true,
  },
  {
    name: 'annotated_images_count',
    label: t('annotatedImages'),
    field: 'annotated_images_count',
    align: 'center',
    sortable: true,
  },
  {
    name: 'total_annotations_count',
    label: t('totalAnnotations'),
    field: 'total_annotations_count',
    align: 'center',
    sortable: true,
  },
];

function formatDate(dateString: string): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  if (locale.value === 'fr') {
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}
</script>

<style scoped lang="scss">
.review-page {
  padding: 16px;
}
</style>
