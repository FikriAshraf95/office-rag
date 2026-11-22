<script setup lang="ts">
import { TabsList } from 'reka-ui'
import { computed, inject, type HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { tabsKey } from './tabsContext'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
const context = inject(tabsKey, { variant: 'underline' as const, select: () => {} })
const look = computed(() =>
  context.variant === 'segmented'
    ? 'inline-flex max-w-full items-center gap-1 overflow-x-auto rounded-lg bg-surface-sunken p-1'
    : 'flex gap-1 overflow-x-auto border-b',
)
</script>

<template>
  <TabsList :class="cn(look, props.class)"><slot /></TabsList>
</template>
