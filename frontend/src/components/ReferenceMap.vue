<template>
  <div>
    <q-btn
      color="grey-8"
      unelevated
      square
      no-caps
      :label="t('hideReferenceMap')"
      icon="map"
      outline
      v-if="referenceMapShown"
      @click="$emit('hideReferenceMap')"
    />
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

defineProps<{
  referenceMapShown: boolean;
}>();

defineEmits<{
  (e: 'hideReferenceMap'): void;
}>();

const { t } = useI18n();
</script>

<style scoped lang="scss"></style>
