<script setup lang="ts">
import { cva, type VariantProps } from 'class-variance-authority'
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

// A small neutral or semantic chip (design-system §10 "Chip", "Banner" soft colours).
const badge = cva('inline-flex items-center gap-1 rounded-xs px-1.5 py-0.5 text-caption whitespace-nowrap', {
  variants: {
    tone: {
      neutral: 'bg-surface-sunken text-ink-muted',
      brand: 'bg-surface-selected text-brand-ink',
      success: 'bg-success-soft text-success',
      warning: 'bg-warning-soft text-warning',
      danger: 'bg-danger-soft text-danger',
      info: 'bg-info-soft text-info',
    },
  },
  defaultVariants: { tone: 'neutral' },
})

const props = defineProps<{ tone?: VariantProps<typeof badge>['tone']; class?: HTMLAttributes['class'] }>()
</script>

<template>
  <span :class="cn(badge({ tone: props.tone }), props.class)"><slot /></span>
</template>
