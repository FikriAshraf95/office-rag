<script setup lang="ts">
import { SwitchRoot, SwitchThumb } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

// Design-system §10 "Switch": an on/off setting that applies at once. Brand when on. Label it with
// `aria-label` or a `<label for>` pointing at `id`.
const props = defineProps<{ id?: string; disabled?: boolean; class?: HTMLAttributes['class'] }>()
const model = defineModel<boolean>({ default: false })
</script>

<template>
  <SwitchRoot
    :id="props.id"
    v-model="model"
    :disabled="props.disabled"
    :class="
      cn(
        'peer inline-flex h-5 w-9 shrink-0 items-center rounded-full border border-transparent bg-border-strong transition-colors data-[state=checked]:bg-brand disabled:cursor-not-allowed disabled:opacity-50',
        props.class,
      )
    "
  >
    <SwitchThumb
      class="pointer-events-none block size-4 translate-x-0.5 rounded-full bg-surface shadow-sm transition-transform data-[state=checked]:translate-x-4.5"
    />
  </SwitchRoot>
</template>
