<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{ title: string; description?: string; icon?: Component }>()
</script>

<template>
  <div
    class="flex flex-col items-center justify-center gap-3 rounded-lg border bg-surface px-6 py-12 text-center"
  >
    <div
      v-if="icon"
      class="flex size-12 items-center justify-center rounded-full bg-accent/20 text-brand-ink"
    >
      <component :is="icon" class="size-5" aria-hidden="true" />
    </div>
    <h2 class="text-title text-ink">{{ title }}</h2>
    <p v-if="description" class="max-w-md text-body text-ink-muted">{{ description }}</p>
    <div v-if="$slots.default" class="mt-2"><slot /></div>
  </div>
</template>
