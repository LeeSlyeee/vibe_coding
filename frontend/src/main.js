import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 글로벌 스타일 import
import './assets/styles/main.css'

// [DEBUG] 전역 알림 제거됨

const app = createApp(App)

app.use(router)

app.mount('#app')
