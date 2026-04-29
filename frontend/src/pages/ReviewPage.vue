<template>
  <q-page class="annotation-page">
    <q-card class="main-frame">
      <q-card-section v-if="annotationStore.selectedImage" class="map-section">
        <q-splitter v-model="splitterPosition" :limits="referenceMapShown ? [20, 80] : [100, 100]">
          <template v-slot:before>
            <AnnotatedMap
              :reference-map-shown="referenceMapShown"
              @show-reference-map="
                referenceMapShown = true;
                splitterPosition = DEFAULT_SPLITTER_POSITION;
              "
            />
          </template>

          <template v-slot:separator v-if="referenceMapShown">
            <q-avatar color="primary" text-color="white" size="40px" icon="drag_indicator" />
          </template>

          <template v-slot:after v-if="referenceMapShown">
            <ReferenceMap
              :reference-map-shown="referenceMapShown"
              @hide-reference-map="referenceMapShown = false"
            />
          </template>
        </q-splitter>
      </q-card-section>

      <q-card-section v-else class="empty-state">
        <div class="text-h5 text-grey-6">{{ t('noImageSelected') }}</div>
        <div class="text-body1 text-grey-6 q-mt-sm">
          {{ t('noImageSelectedMessage') }}
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAnnotationDataStore } from 'stores/annotation-data';
import AnnotatedMap from 'components/AnnotatedMap.vue';
import ReferenceMap from 'components/ReferenceMap.vue';

const DEFAULT_SPLITTER_POSITION = 50;
const { t } = useI18n();
const annotationStore = useAnnotationDataStore();
const splitterPosition = ref(100);
const referenceMapShown = ref(false);

defineProps<{
  annotatorId?: number;
}>();
</script>

<style scoped lang="scss">
.map-section {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.empty-state {
  height: calc(100vh - 50px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
