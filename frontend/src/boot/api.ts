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

  return fetch(input, {
    ...init,
    headers,
  });
}
