import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

app.use(pinia)
useAuthStore(pinia).initialize()
app.use(router)

app.mount('#app')
