<template>
  <q-page class="admin-page">
    <div class="q-pa-md">
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
        v-model:pagination="tablePagination"
        :rows-per-page-options="[10, 20, 50, 100]"
        :rows-per-page-label="t('itemsPerPage')"
        row-key="id"
        flat
        bordered
        @request="onRequest"
      >
        <template #top>
          <div class="row items-center">
            <div class="text-h6 q-mr-xs">{{ t('usersTableTitle') }}</div>
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
        </template>
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

        <template #body-cell-full_name="props">
          <q-td :props="props">
            <q-icon name="sym_r_person" size="sm" color="grey-7" />
            {{ props.row.full_name }}
          </q-td>
        </template>

        <template #body-cell-created_at="props">
          <q-td :props="props">
            <q-icon name="sym_r_calendar_month" size="sm" color="grey-7" class="q-mr-xs" />
            {{ formatDate(props.row.created_at) }}
          </q-td>
        </template>

        <template #body-cell-annotated_images_count="props">
          <q-td :props="props">
            <q-icon name="sym_r_image" size="sm" color="grey-7" />
            {{ props.row.annotated_images_count }}
          </q-td>
        </template>

        <template #body-cell-non_reviewed_images_count="props">
          <q-td :props="props">
            <q-icon name="sym_r_verified_off" size="sm" color="grey-7" />
            {{ props.row.non_reviewed_images_count }}
          </q-td>
        </template>

        <template #body-cell-total_annotations_count="props">
          <q-td :props="props">
            <q-icon name="sym_r_polyline" size="sm" color="grey-7" />
            {{ props.row.total_annotations_count }}
          </q-td>
        </template>

        <template #pagination="scope">
          <div class="row items-center">
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
import { onMounted, watch, ref, computed } from 'vue';
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

function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return t('never');
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return t('never');

  const diffMs = Date.now() - date.getTime();
  const minutes = Math.floor(diffMs / (1000 * 60));
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (minutes === 0) {
    return t('lastActionNow');
  }
  if (minutes < 60) {
    return t('lastActionMinutesAgo', { minutes });
  }
  if (hours < 24) {
    return t('lastActionHoursAgo', { hours });
  }
  return t('lastActionDaysAgo', { days });
}

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

const columns = computed<TableColumn[]>(() => [
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
    align: 'left',
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
    name: 'last_action_at',
    label: t('userLastAction'),
    field: (row: UserReadWithStats) => formatRelativeTime(row.last_action_at),
    align: 'left',
    sortable: true,
  },
  {
    name: 'annotated_images_count',
    label: t('annotatedImages'),
    field: 'annotated_images_count',
    align: 'left',
    sortable: true,
  },
  {
    name: 'non_reviewed_images_count',
    label: t('nonReviewedImages'),
    field: 'non_reviewed_images_count',
    align: 'left',
    sortable: true,
  },
  {
    name: 'total_annotations_count',
    label: t('totalAnnotations'),
    field: 'total_annotations_count',
    align: 'left',
    sortable: true,
  },
]);
</script>

<style scoped lang="scss"></style>
