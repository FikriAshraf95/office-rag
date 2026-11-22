<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

// Design-system §8: a pulsing block on surface-sunken. Decorative; size it with `class`.
// prefers-reduced-motion is handled globally.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div aria-hidden="true" :class="cn('animate-pulse rounded-md bg-surface-sunken', props.class)" />
</template>
