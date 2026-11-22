<script setup lang="ts">
import { Check } from 'lucide-vue-next'
import { DropdownMenuItemIndicator, DropdownMenuRadioItem, type DropdownMenuRadioItemProps } from 'reka-ui'

defineProps<DropdownMenuRadioItemProps>()
</script>

<template>
  <DropdownMenuRadioItem
    :value="value"
    class="relative flex cursor-default items-center gap-2 rounded-md py-1.5 pr-3 pl-8 text-body outline-none select-none data-[highlighted]:bg-surface-hover"
  >
    <span class="absolute left-2 flex size-4 items-center justify-center">
      <DropdownMenuItemIndicator><Check class="size-4 text-brand-ink" /></DropdownMenuItemIndicator>
    </span>
    <slot />
  </DropdownMenuRadioItem>
</template>
