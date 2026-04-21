import { defineStore } from 'pinia';
import { ref } from 'vue';
import { baseUrl } from 'boot/api';

export const useAuthStore = defineStore(
  'auth',
  () => {
    const code = ref('');
    const userId = ref(0);
    const email = ref('');
    const firstName = ref('');
    const lastName = ref('');
    const isReviewer = ref(false);

    const isAuthenticated = ref(false);

    async function login(
      userEmail: string,
      userFirstName: string,
      userLastName: string,
      userCode: string,
    ) {
      const response = await fetch(`${baseUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: userEmail,
          first_name: userFirstName,
          last_name: userLastName,
          code: userCode,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const user = await response.json();

      code.value = user.access_token || userCode;
      userId.value = user.id;
      email.value = user.email;
      firstName.value = user.first_name;
      lastName.value = user.last_name;
      isReviewer.value = user.is_reviewer;
      isAuthenticated.value = true;

      return user;
    }

    function logout() {
      code.value = '';
      userId.value = 0;
      email.value = '';
      firstName.value = '';
      lastName.value = '';
      isReviewer.value = false;
      isAuthenticated.value = false;
    }

    return {
      code,
      userId,
      email,
      firstName,
      lastName,
      isReviewer,
      isAuthenticated,
      login,
      logout,
    };
  },
  {
    persist: {
      pick: ['code', 'userId', 'email', 'firstName', 'lastName', 'isReviewer', 'isAuthenticated'],
    },
  },
);
