<script setup lang="ts">
import { TooltipContent, TooltipPortal, TooltipProvider, TooltipRoot, TooltipTrigger } from 'reka-ui'
import { Fragment, inject } from 'vue'
import { tooltipHostKey } from './tooltipHost'

// A short hint on hover or keyboard focus. Wrap the trigger; a `disabled` button gets no pointer events,
// so the wrapper span is what the pointer lands on. An empty `text` means no tooltip at all. A test that
// mounts a component alone has no app-root provider, so the tooltip then brings its own.
const props = defineProps<{ text?: string; side?: 'top' | 'right' | 'bottom' | 'left' }>()
const hosted = inject(tooltipHostKey, false)
</script>

<template>
  <slot v-if="!props.text" />
  <component :is="hosted ? Fragment : TooltipProvider" v-else>
    <TooltipRoot>
      <TooltipTrigger as-child>
        <span class="inline-flex"><slot /></span>
      </TooltipTrigger>
      <TooltipPortal>
        <TooltipContent
          :side="props.side ?? 'top'"
          :side-offset="6"
          class="z-60 max-w-64 rounded-md bg-ink px-2 py-1 text-caption text-surface shadow-md"
        >
          {{ props.text }}
        </TooltipContent>
      </TooltipPortal>
    </TooltipRoot>
  </component>
</template>
