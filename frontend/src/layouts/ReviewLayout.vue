<template>
  <q-layout view="hHh Lpr lFf">
    <q-header>
      <q-toolbar class="q-pl-lg">
        <q-img src="/epfl_logo.svg" alt="EPFL Logo" class="logo q-mr-sm" no-spinner />

        <q-toolbar-title> HOSM Nepal – {{ t('appTitle') }} </q-toolbar-title>

        <q-select
          v-model="selectedLang"
          :options="langOptions"
          option-value="value"
          option-label="label"
          emit-value
          map-options
          outlined
          square
          dense
          class="lang-select q-ml-md"
          popup-content-class="lang-select-options"
          @update:model-value="changeLocale"
        />

        <q-btn
          color="grey-6"
          :label="t('logout')"
          icon="logout"
          unelevated
          square
          no-caps
          class="q-ml-md"
          @click="logout"
        />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from 'stores/auth';

const { t, locale } = useI18n();
const authStore = useAuthStore();

const langOptions = [
  { label: 'EN', value: 'en-US' },
  { label: 'FR', value: 'fr' },
];

const selectedLang = ref(locale.value);

watch(locale, (newLocale) => {
  selectedLang.value = newLocale;
});

function changeLocale(newLocale: string) {
  locale.value = newLocale as 'en-US' | 'fr';
  if (typeof window !== 'undefined') {
    localStorage.setItem('app-locale', newLocale);
  }
}

function logout() {
  authStore.logout();
}
</script>
