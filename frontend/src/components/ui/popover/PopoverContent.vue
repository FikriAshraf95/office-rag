<script setup lang="ts">
import { PopoverContent, PopoverPortal, type PopoverContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<PopoverContentProps & { class?: HTMLAttributes['class'] }>(), {
  sideOffset: 4,
  align: 'start',
})
const emit = defineEmits<{
  escapeKeyDown: [event: KeyboardEvent]
  interactOutside: [event: Event]
  openAutoFocus: [event: Event]
  closeAutoFocus: [event: Event]
}>()
</script>

<template>
  <PopoverPortal>
    <PopoverContent
      :side="side"
      :align="align"
      :side-offset="sideOffset"
      :class="
        cn(
          'z-50 rounded-lg border bg-surface-raised p-2 text-ink shadow-md data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:slide-in-from-top-1',
          props.class,
        )
      "
      @escape-key-down="(e: KeyboardEvent) => emit('escapeKeyDown', e)"
      @interact-outside="(e: Event) => emit('interactOutside', e)"
      @open-auto-focus="(e: Event) => emit('openAutoFocus', e)"
      @close-auto-focus="(e: Event) => emit('closeAutoFocus', e)"
    >
      <slot />
    </PopoverContent>
  </PopoverPortal>
</template>
