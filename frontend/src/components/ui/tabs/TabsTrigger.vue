<script setup lang="ts">
import { TabsTrigger } from 'reka-ui'
import { computed, inject, type HTMLAttributes } from 'vue'
import { tabsKey } from './tabsContext'

const props = defineProps<{ value: string; disabled?: boolean; class?: HTMLAttributes['class'] }>()
const context = inject(tabsKey, { variant: 'underline' as const, select: () => {} })
// Plain class lists: cn() would drop `text-body-strong` when a colour class is merged.
const look = computed(() =>
  context.variant === 'segmented'
    ? 'shrink-0 rounded-md px-3 py-1 text-body-strong whitespace-nowrap text-ink-muted transition-colors hover:text-ink data-[state=active]:bg-surface-raised data-[state=active]:text-ink data-[state=active]:shadow-sm disabled:opacity-50'
    : '-mb-px shrink-0 rounded-t-md border-b-2 border-transparent px-3 py-2 text-body-strong whitespace-nowrap text-ink-muted hover:text-ink data-[state=active]:border-brand data-[state=active]:text-brand-ink disabled:opacity-50',
)
</script>

<template>
  <TabsTrigger
    :value="props.value"
    :disabled="props.disabled"
    :class="[look, props.class]"
    @click="context.select(props.value)"
  >
    <slot />
  </TabsTrigger>
</template>
