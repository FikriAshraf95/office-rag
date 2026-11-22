<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Toaster } from 'vue-sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import AppLayout from './layouts/AppLayout.vue'

const router = useRouter()

// Before the first navigation resolves, the route is the empty start location. Render nothing
// until it has resolved, so no page flashes for the wrong route.
const routerReady = ref(false)
void router.isReady().then(() => (routerReady.value = true))
</script>

<template>
  <TooltipProvider>
    <AppLayout v-if="routerReady">
      <RouterView />
    </AppLayout>
  </TooltipProvider>
  <Toaster
    position="bottom-right"
    :duration="5000"
    :toast-options="{
      class: 'bg-surface-raised text-ink border border-border shadow-md rounded-lg text-body',
    }"
  />
</template>
