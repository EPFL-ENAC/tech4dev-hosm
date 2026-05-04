<template>
  <q-select
    v-model="selectedLang"
    :options="langOptions"
    option-value="value"
    option-label="label"
    emit-value
    map-options
    outlined
    dense
    class="lang-select q-ml-md"
    popup-content-class="lang-select-options"
    @update:model-value="changeLocale"
  />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const { locale } = useI18n();

const langOptions = [
  { label: 'EN', value: 'en-US' },
  { label: 'FR', value: 'fr' },
];

const selectedLang = ref(locale.value);

watch(locale, (newLocale) => {
  selectedLang.value = newLocale;
});

function changeLocale(newLocale: string) {
  locale.value = newLocale;
  if (typeof window !== 'undefined') {
    localStorage.setItem('app-locale', newLocale);
  }
}
</script>
