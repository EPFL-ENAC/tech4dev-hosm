<template>
  <q-layout view="hHh LpR lFf">
    <q-header>
      <q-toolbar class="q-pl-lg">
        <q-img src="/epfl_logo.svg" alt="EPFL Logo" class="logo q-mr-sm" />

        <q-toolbar-title> HOSM Nepal – Dataset annotation tools </q-toolbar-title>

        <q-btn flat label="Import" icon="file_download" @click="importData" />
        <q-btn flat label="Export" icon="file_upload" @click="exportData" />
        <q-btn flat label="Tutorial" icon="school" @click="showTutorial" />
        <q-btn flat label="About" icon="info" @click="showAbout" />

        <input
          ref="fileInput"
          type="file"
          accept=".json"
          style="display: none"
          @change="handleFileSelect"
        />

        <TutorialDialog v-model="showTutorialDialog" />
        <AboutDialog v-model="showAboutDialog" />
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
import { useAnnotationDataStore } from 'stores/annotation-data';
import AnnotatedSidebar from 'components/AnnotatedSidebar.vue';
import TutorialDialog from 'components/TutorialDialog.vue';
import AboutDialog from 'components/AboutDialog.vue';

const annotationStore = useAnnotationDataStore();
const leftDrawerOpen = ref(true);
const showTutorialDialog = ref(false);
const showAboutDialog = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

function showTutorial() {
  showTutorialDialog.value = true;
}

function showAbout() {
  showAboutDialog.value = true;
}

function exportData() {
  annotationStore.exportData();
}

function importData() {
  fileInput.value?.click();
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    annotationStore.importData(file);
    target.value = '';
  }
}
</script>
<style lang="scss">
.logo {
  width: 96px;
  height: auto;
  object-fit: contain;
}
</style>
