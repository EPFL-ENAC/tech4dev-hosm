<template>
  <q-page class="login-page">
    <div class="login-container">
      <q-card>
        <q-card-section>
          <div class="text-h5">{{ t('login') }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="onSubmit" class="q-gutter-md">
            <q-input
              v-model="form.email"
              :label="t('emailLabel') + ' *'"
              type="email"
              lazy-rules
              :rules="[
                (val) => !!val || t('emailRequired'),
                (val) => /.+@.+\..+/.test(val) || t('emailInvalid'),
              ]"
            />

            <q-input
              v-model="form.firstName"
              :label="t('firstNameLabel') + ' *'"
              lazy-rules
              :rules="[(val) => !!val || t('firstNameRequired')]"
            />

            <q-input
              v-model="form.lastName"
              :label="t('lastNameLabel') + ' *'"
              lazy-rules
              :rules="[(val) => !!val || t('lastNameRequired')]"
            />

            <q-input
              v-model="form.code"
              type="password"
              :label="t('codeLabel') + ' *'"
              lazy-rules
              :rules="[(val) => !!val || t('codeRequired')]"
            />

            <q-btn :label="t('login')" type="submit" color="primary" :loading="loading" />
          </q-form>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from 'stores/auth';
import { useAnnotationDataStore } from 'stores/annotation-data';

const $q = useQuasar();
const router = useRouter();
const authStore = useAuthStore();
const annotationStore = useAnnotationDataStore();
const { t } = useI18n();

const loading = ref(false);

const form = reactive({
  email: '',
  firstName: '',
  lastName: '',
  code: '',
});

async function onSubmit() {
  loading.value = true;

  try {
    const user = await authStore.login(form.email, form.firstName, form.lastName, form.code);

    $q.notify({
      type: 'positive',
      message: t('welcomeMessage', { name: user.first_name }),
    });

    await annotationStore.loadAnnotations();

    if (user.is_reviewer) {
      await router.replace('/review');
    } else {
      await router.replace('/');
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error instanceof Error ? error.message : t('loginFailed'),
    });
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped lang="scss">
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
}

.login-container {
  width: 100%;
  max-width: 400px;
}
</style>
