<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Toaster } from 'vue-sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import LoginPage from '@/features/auth/LoginPage.vue'
import { useUserStore } from '@/stores/user'
import AppLayout from './layouts/AppLayout.vue'

const router = useRouter()
const user = useUserStore()

// Before the first navigation resolves, the route is the empty start location. Render nothing
// until it has resolved, so no page flashes for the wrong route.
const routerReady = ref(false)
void router.isReady().then(() => (routerReady.value = true))

// `/config` says the auth mode. Until it answers, render nothing, so password mode never flashes the
// shell before the login page (SPEC-07 §8).
onMounted(() => {
  if (!user.config) void user.load()
})
const configReady = computed(() => !!user.config || !!user.error)
</script>

<template>
  <TooltipProvider>
    <template v-if="routerReady && configReady">
      <LoginPage v-if="user.needsLogin" />
      <AppLayout v-else>
        <RouterView />
      </AppLayout>
    </template>
  </TooltipProvider>
  <Toaster
    position="bottom-right"
    :duration="5000"
    :toast-options="{
      class: 'bg-surface-raised text-ink border border-border shadow-md rounded-lg text-body',
    }"
  />
</template>
