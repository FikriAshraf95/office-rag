import { createPinia } from 'pinia'
import { createApp } from 'vue'
import { toast } from 'vue-sonner'
import 'vue-sonner/style.css'
import '@/styles/tailwind.css'
import { configureHttp } from '@/api/http'
import { applyTheme, readStoredTheme, watchSystemTheme } from '@/lib/theme'
import { useUserStore } from '@/stores/user'
import App from './App.vue'
import { router } from './router'

const app = createApp(App)
app.use(createPinia())

// The API client sends the chosen demo user and toasts errors (SPEC-07 §3, §8).
const user = useUserStore()
configureHttp({
  demoUser: () => user.userId,
  toastError: (message) => toast.error(message),
})

applyTheme(readStoredTheme())
watchSystemTheme(readStoredTheme)

app.use(router)
app.mount('#app')
