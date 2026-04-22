import { getI18nT } from 'src/utils/i18n';

interface CustomWindow extends Window {
  env: {
    API_URL: string;
    API_PATH: string;
  };
}

const appEnv = (window as unknown as CustomWindow).env;
export const baseUrl = `${appEnv.API_URL}${appEnv.API_PATH}`;

export async function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const authStore = await import('stores/auth').then((m) => m.useAuthStore());
  const code = authStore.code;

  const headers = new Headers(init?.headers);
  if (code) {
    headers.set('Authorization', `Bearer ${code}`);
  }

  const response = await fetch(input, {
    ...init,
    headers,
  });

  if (response.status === 401) {
    authStore.logout();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  } else if (response.status === 403) {
    if (typeof window !== 'undefined') {
      const { Notify } = await import('quasar');
      Notify.create({
        type: 'negative',
        message: getI18nT()('Not authorized to perform this action'),
      });
    }
  }

  return response;
}
