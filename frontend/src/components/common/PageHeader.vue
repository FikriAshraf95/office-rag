<script setup lang="ts">
defineProps<{ title: string; description?: string }>()
</script>

<template>
  <header class="flex flex-wrap items-end justify-between gap-4 pb-6">
    <div class="min-w-0">
      <h1 class="truncate text-display text-ink">{{ title }}</h1>
      <p v-if="description" class="mt-1 text-body text-ink-muted">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="flex items-center gap-2"><slot name="actions" /></div>
  </header>
</template>
