<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="q-dialog-plugin">
      <q-card-section>
        <div class="text-h6">{{ t('exportAnnotations') }}</div>
      </q-card-section>

      <q-card-section></q-card-section>

      <q-card-actions align="right">
        <q-btn flat :label="t('close')" color="primary" @click="onCloseClick" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useDialogPluginComponent } from 'quasar';

const { t } = useI18n();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogCancel } = useDialogPluginComponent();

function onCloseClick() {
  onDialogCancel();
}
</script>
