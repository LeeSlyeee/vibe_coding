import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.mooddiary.app',
  appName: 'MoodDiary',
  webDir: 'dist',
  plugins: {
    CapacitorHttp: {
      enabled: true,
    },
  },
  // [여기 추가]
  server: {
    url: 'https://217.142.253.35.nip.io', // 여기에 OCI 주소 입력
    cleartext: true
  }
};

export default config;
