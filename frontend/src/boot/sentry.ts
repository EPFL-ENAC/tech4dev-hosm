import { defineBoot } from '#q-app/wrappers';
import * as Sentry from '@sentry/vue';

interface CustomWindow extends Window {
  env: {
    SENTRY_ENVIRONMENT?: string;
    SENTRY_RATE?: string;
  };
}

export default defineBoot(({ app }) => {
  const appEnv = (window as unknown as CustomWindow).env;

  Sentry.init({
    app,
    dsn: 'https://b31134f16f654bbfbf56c48581e92d26@enac-it-glitchtip.epfl.ch/4',
    environment: appEnv.SENTRY_ENVIRONMENT ?? 'prod',
    tracesSampleRate: parseFloat(appEnv.SENTRY_RATE ?? '1.00'),
  });
});
