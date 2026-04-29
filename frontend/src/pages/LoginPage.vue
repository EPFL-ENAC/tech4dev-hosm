<template>
  <q-page class="login-page">
    <div class="login-container">
      <q-card class="q-pa-md" flat bordered>
        <q-card-section>
          <div class="text-h5">{{ t('appTitle') }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="onSubmit" class="q-gutter-md">
            <q-input
              v-model="form.email"
              :placeholder="t('emailLabel')"
              dense
              type="email"
              lazy-rules
              :rules="[
                (val) => !!val || t('emailRequired'),
                (val) => /.+@.+\..+/.test(val) || t('emailInvalid'),
              ]"
            >
              <template v-slot:prepend>
                <q-icon name="email" />
              </template>
            </q-input>

            <q-input
              v-model="form.fullName"
              :placeholder="t('fullNameLabel')"
              dense
              type="text"
              lazy-rules
              :rules="[(val) => !!val || t('fullNameRequired')]"
            >
              <template v-slot:prepend>
                <q-icon name="person" />
              </template>
            </q-input>

            <q-input
              v-model="form.code"
              :type="showPassword ? 'text' : 'password'"
              :placeholder="t('codeLabel')"
              outlined
              lazy-rules
              :rules="[(val) => !!val || t('codeRequired')]"
            >
              <template v-slot:prepend>
                <q-icon name="lock" />
              </template>
              <template v-slot:append>
                <q-icon
                  :name="showPassword ? 'visibility' : 'visibility_off'"
                  class="cursor-pointer"
                  @click="showPassword = !showPassword"
                />
              </template>
            </q-input>

            <q-btn
              :label="t('login')"
              type="submit"
              color="primary"
              unelevated
              no-caps
              :loading="loading"
              class="q-px-lg"
            />
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
const showPassword = ref(false);

const form = reactive({
  email: '',
  fullName: '',
  code: '',
});

async function onSubmit() {
  loading.value = true;

  try {
    const user = await authStore.login(form.email, form.fullName, form.code);

    $q.notify({
      type: 'positive',
      message: t('welcomeMessage', { name: user.full_name }),
    });

    await annotationStore.loadAnnotations();

    if (user.is_reviewer) {
      await router.replace({ path: '/admin' });
    } else {
      await router.replace({ path: '/' });
    }
  } catch (error) {
    let errorMessage = t('loginFailed');

    if (error instanceof Error) {
      const errorDetail = (error as { errorDetail?: unknown }).errorDetail;

      if (typeof errorDetail === 'object' && errorDetail) {
        const detail = errorDetail as Record<string, unknown>;

        if (detail['code'] === 'email_exists_name_mismatch') {
          errorMessage = t('emailExistsNameMismatch');
        }
      } else if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      } else if (error.message) {
        errorMessage = error.message;
      }
    }

    $q.notify({
      type: 'negative',
      message: errorMessage,
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
  background-color: $grey-2;
}

.login-container {
  width: 100%;
  max-width: 400px;
  text-align: center;
}
</style>
