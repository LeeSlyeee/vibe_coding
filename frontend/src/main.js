import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 글로벌 스타일 import
import './assets/styles/main.css'

const app = createApp(App)

app.use(router)

app.mount('#app')
