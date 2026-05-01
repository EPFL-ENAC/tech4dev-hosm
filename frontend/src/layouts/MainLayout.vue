<template>
  <q-layout view="hHh LpR lFf">
    <q-header>
      <q-toolbar class="q-px-md">
        <LogosLine />

        <q-toolbar-title> {{ t('appTitle') }} </q-toolbar-title>

        <q-btn
          v-if="userIsReviewer"
          flat
          :label="t('backToAdminPage')"
          icon="navigate_before"
          to="/admin"
        />
        <q-btn flat :label="t('tutorial')" icon="school" @click="showTutorial" />
        <q-btn flat :label="t('about')" icon="info" @click="showAbout" />

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

        <TutorialDialog v-model="showTutorialDialog" />
        <AboutDialog v-model="showAboutDialog" />
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
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from 'stores/auth';
import AnnotatedSidebar from 'components/AnnotatedSidebar.vue';
import TutorialDialog from 'components/TutorialDialog.vue';
import AboutDialog from 'components/AboutDialog.vue';
import LanguageSelector from 'components/LanguageSelector.vue';
import LogosLine from 'components/LogosLine.vue';

const { t } = useI18n();
const leftDrawerOpen = ref(true);
const showTutorialDialog = ref(false);
const showAboutDialog = ref(false);
const authStore = useAuthStore();
const userIsReviewer = authStore.isReviewer;

function showTutorial() {
  showTutorialDialog.value = true;
}

function showAbout() {
  showAboutDialog.value = true;
}

function logout() {
  authStore.logout();
}
</script>

<style lang="scss" scoped>
body {
  overflow: hidden !important;
}
</style>
