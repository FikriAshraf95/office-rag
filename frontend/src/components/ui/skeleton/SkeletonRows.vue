<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import Skeleton from './Skeleton.vue'

// A loading placeholder of stacked rows. With `cols` above 1 each row is a line of cells, like a table.
// The sr-only label keeps the state readable to assistive tech and to tests.
const props = withDefaults(
  defineProps<{ rows?: number; cols?: number; label?: string; class?: HTMLAttributes['class'] }>(),
  { rows: 3, cols: 1, label: 'Loading…' },
)
</script>

<template>
  <div role="status" :class="cn('flex flex-col gap-3', props.class)">
    <span class="sr-only">{{ props.label }}</span>
    <div v-for="r in props.rows" :key="r" class="flex gap-4" aria-hidden="true">
      <Skeleton
        v-for="c in props.cols"
        :key="c"
        class="h-5 flex-1"
        :class="c === 1 && props.cols > 1 && 'flex-[2]'"
      />
    </div>
  </div>
</template>
