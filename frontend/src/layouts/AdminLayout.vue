<template>
  <q-layout view="hHh Lpr lFf">
    <q-header>
      <q-toolbar class="q-px-md">
        <LogosLine />

        <q-toolbar-title> {{ t('adminPageTitle') }} </q-toolbar-title>

        <q-btn
          flat
          :label="t('downloadJson')"
          icon="download"
          :loading="isDownloading"
          :disable="isDownloading"
          @click="downloadAnnotations"
        >
          <template #loading>
            <q-spinner class="on-left" />
            {{ t('downloadJson') }}
          </template>
        </q-btn>

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
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { useAuthStore } from 'stores/auth';
import { baseUrl, authFetch } from 'boot/api';
import LanguageSelector from 'components/LanguageSelector.vue';
import LogosLine from 'components/LogosLine.vue';

const { t } = useI18n();
const authStore = useAuthStore();
const isDownloading = ref(false);

function logout() {
  authStore.logout();
}

async function downloadAnnotations() {
  isDownloading.value = true;
  try {
    const response = await authFetch(`${baseUrl}/annotations/download`, {
      method: 'GET',
    });

    if (!response.ok) {
      Notify.create({ type: 'negative', message: t('failedToDownloadAnnotations') });
      return;
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nepal_damage_annotations.json';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch {
    Notify.create({ type: 'negative', message: t('failedToDownloadAnnotations') });
  } finally {
    isDownloading.value = false;
  }
}
</script>
