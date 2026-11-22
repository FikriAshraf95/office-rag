<script setup lang="ts">
import { Check, ChevronDown } from 'lucide-vue-next'
import {
  SelectContent,
  SelectItem,
  SelectItemIndicator,
  SelectItemText,
  SelectLabel,
  SelectPortal,
  SelectRoot,
  SelectTrigger,
  SelectViewport,
} from 'reka-ui'
import { computed, useAttrs, useSlots, type HTMLAttributes } from 'vue'
import { fieldClass } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { matchOption, readOptions, type SelectOption } from './options'

// A styled select with a popup list. Options are plain `<option>` and `<optgroup>` children. Items use
// their index as the value, because reka refuses an empty string and `<option value="">` is common.
// `class` sizes the trigger; every other attribute (id, aria-label, data-testid) goes to it too, so a
// FormField label points at it.
defineOptions({ inheritAttrs: false })
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
const model = defineModel<string>()
const attrs = useAttrs()
const slots = useSlots()

function groupsOf(options: SelectOption[]) {
  const groups: { name?: string; items: { option: SelectOption; index: number }[] }[] = []
  options.forEach((option, index) => {
    const last = groups.at(-1)
    if (last && last.name === option.group) last.items.push({ option, index })
    else groups.push({ name: option.group, items: [{ option, index }] })
  })
  return groups
}

const view = computed(() => {
  const options = readOptions(slots.default?.())
  const index = matchOption(options, model.value)
  return { options, index, selected: options[index], groups: groupsOf(options) }
})

const isDisabled = () => attrs.disabled !== undefined && attrs.disabled !== false

function choose(value: unknown) {
  const option = view.value.options[Number(value)]
  if (option) model.value = option.value as string
}
</script>

<template>
  <SelectRoot
    :model-value="view.index < 0 ? '' : String(view.index)"
    :disabled="isDisabled()"
    @update:model-value="choose"
  >
    <SelectTrigger
      v-bind="$attrs"
      :data-value="view.selected?.value ?? ''"
      :class="
        cn(
          fieldClass,
          'flex h-(--control-h) w-full items-center justify-between gap-2 pr-2 pl-3 text-left',
          props.class,
        )
      "
    >
      <span :class="['min-w-0 truncate', view.selected?.disabled && 'text-ink-subtle']">{{
        view.selected?.label
      }}</span>
      <ChevronDown class="size-4 shrink-0 text-ink-muted" aria-hidden="true" />
    </SelectTrigger>
    <SelectPortal>
      <SelectContent
        position="popper"
        :side-offset="4"
        class="z-50 max-h-(--reka-select-content-available-height) min-w-(--reka-select-trigger-width) overflow-hidden rounded-lg border bg-surface-raised text-ink shadow-md data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:slide-in-from-top-1"
      >
        <SelectViewport class="max-h-80 p-1">
          <template v-for="(group, g) in view.groups" :key="g">
            <SelectLabel v-if="group.name" class="px-2.5 pt-2 pb-1 text-caption text-ink-muted">{{
              group.name
            }}</SelectLabel>
            <SelectItem
              v-for="{ option, index } in group.items"
              :key="index"
              :value="String(index)"
              :disabled="option.disabled"
              :data-value="option.value ?? ''"
              class="flex cursor-default items-center justify-between gap-3 rounded-md px-2.5 py-1.5 text-body outline-none select-none data-[disabled]:opacity-50 data-[highlighted]:bg-surface-hover data-[state=checked]:bg-surface-selected data-[state=checked]:text-brand-ink"
            >
              <SelectItemText>{{ option.label }}</SelectItemText>
              <SelectItemIndicator><Check class="size-4" aria-hidden="true" /></SelectItemIndicator>
            </SelectItem>
          </template>
        </SelectViewport>
      </SelectContent>
    </SelectPortal>
  </SelectRoot>
</template>
