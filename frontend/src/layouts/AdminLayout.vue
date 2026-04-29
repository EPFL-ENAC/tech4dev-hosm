<template>
  <q-layout view="hHh Lpr lFf">
    <q-header>
      <q-toolbar class="q-pl-lg">
        <q-img src="/epfl_logo.svg" alt="EPFL Logo" class="logo q-mr-sm" no-spinner />

        <q-toolbar-title> HOSM Nepal – {{ t('appTitle') }} </q-toolbar-title>

        <LanguageSelector />

        <q-btn
          color="grey-8"
          :label="t('logout')"
          icon="logout"
          outline
          unelevated
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
import { useI18n } from 'vue-i18n';
import { useAuthStore } from 'stores/auth';
import LanguageSelector from 'components/LanguageSelector.vue';

const { t } = useI18n();
const authStore = useAuthStore();

function logout() {
  authStore.logout();
}
</script>
