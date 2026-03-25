<template>
  <q-layout view="hHh LpR lFf">
    <q-header>
      <q-toolbar class="q-pl-lg">
        <q-img src="/epfl_logo.svg" alt="EPFL Logo" class="logo q-mr-sm" />

        <q-toolbar-title> HOSM Nepal – Dataset annotation tools </q-toolbar-title>

        <q-btn flat label="Export Annotations" icon="file_download" @click="showExport" />
        <q-btn flat label="Tutorial" icon="school" @click="showTutorial" />
        <q-btn flat label="About" icon="info" @click="showAbout" />

        <TutorialDialog v-model="showTutorialDialog" />
        <AboutDialog v-model="showAboutDialog" />
        <ExportDialog v-model="showExportDialog" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" :breakpoint="0" bordered>
      <AnnotatedSidebar />
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import AnnotatedSidebar from 'components/AnnotatedSidebar.vue';
import TutorialDialog from 'components/TutorialDialog.vue';
import AboutDialog from 'components/AboutDialog.vue';
import ExportDialog from 'components/ExportDialog.vue';

const leftDrawerOpen = ref(true);
const showTutorialDialog = ref(false);
const showAboutDialog = ref(false);
const showExportDialog = ref(false);

function showTutorial() {
  showTutorialDialog.value = true;
}

function showAbout() {
  showAboutDialog.value = true;
}

function showExport() {
  showExportDialog.value = true;
}
</script>
<style lang="scss">
.logo {
  width: 96px;
  height: auto;
  object-fit: contain;
}
</style>
