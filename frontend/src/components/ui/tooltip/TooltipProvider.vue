<script setup lang="ts">
import { TooltipProvider } from 'reka-ui'
import { provide } from 'vue'
import { tooltipHostKey } from './tooltipHost'

// Mounted once at the app root (App.vue): one delay and one "skip the delay when moving between
// tooltips" rule for the whole app.
provide(tooltipHostKey, true)
</script>

<template>
  <TooltipProvider :delay-duration="300" :skip-delay-duration="200"><slot /></TooltipProvider>
</template>
