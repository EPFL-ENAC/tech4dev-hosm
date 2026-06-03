<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="q-dialog-plugin terms-dialog">
      <q-card-section>
        <div class="text-h6">{{ t('termsAndConditionsTitle') }}</div>
      </q-card-section>

      <q-card-section class="q-px-md">
        <div v-html="t('termsAndConditionsContent')" />
      </q-card-section>

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

<style lang="scss" scoped>
.terms-dialog {
  width: 80vw;
  max-width: 600px;
}
</style>
