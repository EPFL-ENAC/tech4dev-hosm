<template>
  <q-page class="login-page">
    <div class="login-container">
      <q-card>
        <q-card-section>
          <div class="text-h5">Login</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="onSubmit" class="q-gutter-md">
            <q-input
              v-model="form.email"
              label="Email *"
              type="email"
              lazy-rules
              :rules="[
                (val) => !!val || 'Email is required',
                (val) => /.+@.+\..+/.test(val) || 'Enter a valid email',
              ]"
            />

            <q-input
              v-model="form.firstName"
              label="First Name *"
              lazy-rules
              :rules="[(val) => !!val || 'First name is required']"
            />

            <q-input
              v-model="form.lastName"
              label="Last Name *"
              lazy-rules
              :rules="[(val) => !!val || 'Last name is required']"
            />

            <q-input
              v-model="form.code"
              type="password"
              label="Code *"
              lazy-rules
              :rules="[(val) => !!val || 'Code is required']"
            />

            <q-btn label="Login" type="submit" color="primary" :loading="loading" />
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
import { useAuthStore } from 'stores/auth';
import { useAnnotationDataStore } from 'stores/annotation-data';

const $q = useQuasar();
const router = useRouter();
const authStore = useAuthStore();
const annotationStore = useAnnotationDataStore();

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
      message: `Welcome, ${user.first_name}!`,
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
      message: error instanceof Error ? error.message : 'Login failed',
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
