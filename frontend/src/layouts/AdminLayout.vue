<template>
  <q-layout view="hHh Lpr lFf">
    <q-header>
      <q-toolbar class="q-pl-md">
        <LogosLine />

        <q-toolbar-title> {{ t('adminPageTitle') }} </q-toolbar-title>

        <q-btn flat :label="t('toAnnotationPage')" icon="navigate_next" to="/" />

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
import LogosLine from 'components/LogosLine.vue';

const { t } = useI18n();
const authStore = useAuthStore();

function logout() {
  authStore.logout();
}
</script>
