<script setup lang="ts">
import { computed } from 'vue'
import { labelSoftClasses, type LabelColor } from '@/lib/colors'
import { cn } from '@/lib/utils'

// A status value (design-system §10): a soft pill with a dot in the ink colour and the label text.
const props = defineProps<{ color?: string | null; label: string; class?: string }>()

const tint = computed(() => labelSoftClasses[(props.color ?? '') as LabelColor] ?? labelSoftClasses.grey)
</script>

<template>
  <span
    :class="
      cn(
        'inline-flex h-[26px] max-w-full items-center gap-1.5 rounded-full px-2.5 text-cell font-medium whitespace-nowrap',
        tint,
        props.class,
      )
    "
    :title="label"
  >
    <span class="size-1.5 shrink-0 rounded-full bg-current" aria-hidden="true" />
    <span class="truncate">{{ label }}</span>
  </span>
</template>
