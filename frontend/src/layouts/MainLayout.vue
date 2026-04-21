<template>
  <q-layout view="hHh LpR lFf">
    <q-header>
      <q-toolbar class="q-pl-lg">
        <q-img src="/epfl_logo.svg" alt="EPFL Logo" class="logo q-mr-sm" no-spinner />

        <q-toolbar-title> HOSM Nepal – {{ t('appTitle') }} </q-toolbar-title>

        <q-btn flat :label="t('tutorial')" icon="school" @click="showTutorial" />
        <q-btn flat :label="t('about')" icon="info" @click="showAbout" />

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
import { ref, watch, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAnnotationDataStore } from 'stores/annotation-data';
import AnnotatedSidebar from 'components/AnnotatedSidebar.vue';
import TutorialDialog from 'components/TutorialDialog.vue';
import AboutDialog from 'components/AboutDialog.vue';

const { t, locale } = useI18n();
const leftDrawerOpen = ref(true);
const showTutorialDialog = ref(false);
const showAboutDialog = ref(false);
const annotationStore = useAnnotationDataStore();

onMounted(async () => {
  if (annotationStore.annotatedImages.length === 0) {
    await annotationStore.loadAnnotations();
  }
});

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

function showTutorial() {
  showTutorialDialog.value = true;
}

function showAbout() {
  showAboutDialog.value = true;
}
</script>
<style lang="scss">
.logo {
  width: 96px;
  height: auto;
  object-fit: contain;
}

.lang-select .q-field__native {
  font-weight: 500;
  font-size: 0.85rem;
}

.lang-select-options {
  box-shadow: none;
  border: 1px solid #e6e6e6;
  border-radius: none;
}

.lang-select-options .q-item__label {
  font-weight: 500;
  font-size: 0.85rem;
}
</style>
