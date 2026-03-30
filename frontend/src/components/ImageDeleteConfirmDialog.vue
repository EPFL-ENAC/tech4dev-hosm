<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="q-dialog-plugin">
      <q-card-section>
        <div class="text-h6">{{ title }}</div>
      </q-card-section>

      <q-card-section>
        <p>{{ message }}</p>
        <q-checkbox v-model="rememberChoice">
          Don't ask again during this session
        </q-checkbox>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Cancel" color="grey" @click="onCancelClick" />
        <q-btn flat label="OK" color="primary" @click="onOKClick" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useDialogPluginComponent } from 'quasar';

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();

defineProps({
  title: { type: String, required: true },
  message: { type: String, required: true }
});

const rememberChoice = ref(false);

function onOKClick() {
  onDialogOK(rememberChoice.value);
}

function onCancelClick() {
  onDialogCancel();
}
</script>
