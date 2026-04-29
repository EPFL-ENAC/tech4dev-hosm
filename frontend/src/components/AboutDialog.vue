<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="q-dialog-plugin">
      <q-card-section>
        <div class="text-h6">{{ t('aboutTitle') }}</div>
      </q-card-section>

      <q-card-section class="q-px-md">
        <p>{{ t('aboutJointEffort') }}</p>

        <I18nT keypath="aboutDevelopment" tag="p">
          <template #link>
            <a
              href="https://enac-it4r.epfl.ch/"
              target="_blank"
              rel="noopener"
              class="text-primary"
            >
              ENAC-IT4R
            </a>
          </template>
        </I18nT>

        <I18nT keypath="aboutRepository" tag="p">
          <template #link>
            <a
              href="https://github.com/EPFL-ENAC/tech4dev-hosm/"
              target="_blank"
              rel="noopener"
              class="text-primary"
            >
              GitHub
            </a>
          </template>
        </I18nT>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat :label="t('close')" color="primary" @click="onCloseClick" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { I18nT } from 'vue-i18n';
import { useDialogPluginComponent } from 'quasar';

const { t } = useI18n();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogCancel } = useDialogPluginComponent();

function onCloseClick() {
  onDialogCancel();
}
</script>
