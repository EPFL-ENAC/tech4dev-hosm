<template>
  <q-layout view="hHh LpR lFf">
    <q-header>
      <q-toolbar class="q-pl-lg">
        <LogosLine />

        <q-toolbar-title> {{ t('reviewPageTitle') }} </q-toolbar-title>

        <q-btn flat :label="t('backToAdminPage')" icon="arrow_back" to="/admin" />

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

    <q-drawer v-model="leftDrawerOpen" :breakpoint="0" :width="314" bordered>
      <AnnotatedSidebar />
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAnnotationDataStore } from 'stores/annotation-data';
import { useAuthStore } from 'stores/auth';
import AnnotatedSidebar from 'components/AnnotatedSidebar.vue';
import LanguageSelector from 'components/LanguageSelector.vue';
import LogosLine from 'components/LogosLine.vue';

const { t } = useI18n();
const leftDrawerOpen = ref(true);
const annotationStore = useAnnotationDataStore();
const authStore = useAuthStore();

onMounted(async () => {
  if (annotationStore.annotatedImages.length === 0) {
    await annotationStore.loadAnnotations();
  }
});

function logout() {
  authStore.logout();
}
</script>

<style lang="scss">
body {
  overflow: hidden !important;
}
</style>
