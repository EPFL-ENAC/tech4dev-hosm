<template>
  <q-page class="review-page">
    <div class="text-h5">{{ t('reviewPage') }}</div>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>

<style scoped lang="scss">
.review-page {
  padding: 16px;
}
</style>
