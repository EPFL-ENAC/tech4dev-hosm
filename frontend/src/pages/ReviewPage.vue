<template>
  <q-page class="review-page">
    <div class="q-pa-md">
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
        :title="t('usersTableTitle')"
        :rows="usersStore.users"
        :columns="columns"
        :loading="usersStore.loading"
        v-model:pagination="tablePagination"
        :rows-per-page-options="[10, 20, 50, 100]"
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

        <template #pagination="scope">
          <div class="row items-center q-pa-sm">
            <q-btn
              v-if="scope.pagesNumber > 2"
              icon="first_page"
              color="grey-8"
              round
              dense
              flat
              :disable="scope.isFirstPage"
              @click="scope.firstPage"
            />
            <q-btn
              icon="chevron_left"
              color="grey-8"
              round
              dense
              flat
              :disable="scope.isFirstPage"
              @click="scope.prevPage"
            />
            <span class="q-mx-md">
              {{ t('page') }} {{ scope.pagination.page }} {{ t('of') }} {{ scope.pagesNumber }}
            </span>
            <q-btn
              icon="chevron_right"
              color="grey-8"
              round
              dense
              flat
              :disable="scope.isLastPage"
              @click="scope.nextPage"
            />
            <q-btn
              v-if="scope.pagesNumber > 2"
              icon="last_page"
              color="grey-8"
              round
              dense
              flat
              :disable="scope.isLastPage"
              @click="scope.lastPage"
            />
          </div>
        </template>
      </q-table>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { onMounted, watch, ref } from 'vue';
import { useUsersStore } from 'stores/users';
import { useDateFormat } from '../composables/useDateFormat';
import type { UserReadWithStats } from '../models';

interface PaginationSettings {
  rowsPerPage: number;
  page: number;
  sortBy?: string | null;
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

// Reactive pagination object for v-model binding with server-side pagination
// rowsNumber is required for server-side pagination
const tablePagination = ref({
  page: 1,
  rowsPerPage: 20,
  sortBy: 'full_name',
  descending: false,
  rowsNumber: 0,
});

// Sync store pagination to table pagination when fetched
watch(
  () => [usersStore.pagination.page, usersStore.pagination.pageSize, usersStore.pagination.total],
  () => {
    tablePagination.value.page = usersStore.pagination.page;
    tablePagination.value.rowsPerPage = usersStore.pagination.pageSize;
    tablePagination.value.rowsNumber = usersStore.pagination.total;
  },
);

onMounted(async () => {
  await usersStore.fetchUsers();
});

async function onRequest(props: { pagination: PaginationSettings }) {
  const { page, rowsPerPage, sortBy, descending } = props.pagination;

  // Sync the table pagination ref with the request props
  tablePagination.value.page = page;
  tablePagination.value.rowsPerPage = rowsPerPage;
  tablePagination.value.sortBy = sortBy || 'full_name';
  tablePagination.value.descending = descending ?? false;

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
