import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.mooddiary.app',
  appName: 'haruON',
  webDir: 'dist',
  plugins: {
    CapacitorHttp: {
      enabled: false,
    },
  },
};

export default config;
