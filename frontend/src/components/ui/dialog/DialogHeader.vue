<script setup lang="ts">
import { DialogDescription, DialogTitle } from 'reka-ui'

defineProps<{ title: string; description?: string }>()
</script>

<template>
  <div class="px-6 pt-5 pb-1 pr-14">
    <DialogTitle class="text-title text-ink">{{ title }}</DialogTitle>
    <DialogDescription v-if="description" class="mt-0.5 text-body text-ink-muted">{{
      description
    }}</DialogDescription>
  </div>
</template>
