<template>
  <q-page class="review-page">
    <div class="q-pa-md">
      <div class="text-h5 q-mb-md">{{ t('usersTableTitle') }}</div>

      <div class="row q-mb-md">
        <q-space />
        <q-btn
          flat
          round
          icon="refresh"
          color="primary"
          :loading="usersStore.loading"
          @click="usersStore.fetchUsers()"
        >
          <q-tooltip>{{ t('refresh') }}</q-tooltip>
        </q-btn>
      </div>

      <q-banner v-if="usersStore.error" class="rounded-borders bg-negative text-white q-mb-md">
        <template #avatar>
          <q-icon name="error" color="white" />
        </template>
        {{ t('errorLoadingUsers') }}
        <template #action>
          <q-btn flat color="white" label="Retry" @click="usersStore.fetchUsers()" />
        </template>
      </q-banner>

      <q-table
        :rows="usersStore.users"
        :columns="columns"
        :loading="usersStore.loading"
        :pagination="tablePagination"
        :rows-per-page-options="[20, 50, 100]"
        row-key="id"
        flat
        bordered
        @request="onRequest"
      >
        <template #no-data>
          <div class="full-width flex-center q-pa-md">
            <div class="text-grey-7">
              {{ usersStore.error ? t('errorLoadingUsers') : t('noUsersFound') }}
            </div>
          </div>
        </template>

        <template #body-cell-role="props">
          <q-td :props="props">
            <q-badge :color="props.row.is_reviewer ? 'primary' : 'grey-7'">
              {{ props.row.is_reviewer ? t('roleReviewer') : t('roleAnnotator') }}
            </q-badge>
          </q-td>
        </template>
      </q-table>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { onMounted, computed } from 'vue';
import { useUsersStore } from 'stores/users';
import { useDateFormat } from '../composables/useDateFormat';
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

const { t } = useI18n();
const usersStore = useUsersStore();
const { formatDate } = useDateFormat();

// Computed property to sync Quasar table pagination with store state
// Note: rowsNumber is omitted for server-side pagination to avoid incorrect scroll calculations
const tablePagination = computed(() => ({
  page: usersStore.pagination.page,
  rowsPerPage: usersStore.pagination.pageSize,
  sortBy: usersStore.pagination.sortBy,
  descending: usersStore.pagination.descending,
}));

onMounted(async () => {
  await usersStore.fetchUsers();
});

async function onRequest(props: { pagination: PaginationSettings }) {
  const { page, rowsPerPage, sortBy, descending } = props.pagination;

  await usersStore.setPagination({
    page,
    pageSize: rowsPerPage,
    sortBy: sortBy || 'full_name',
    descending: descending ?? false,
  });
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
    field: (row: UserReadWithStats) => formatDate(row.created_at),
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
</script>

<style scoped lang="scss">
.review-page {
  /* Padding is handled by q-pa-md on the inner div */
}
</style>
