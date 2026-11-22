<script setup lang="ts">
import { TabsRoot } from 'reka-ui'
import { provide, reactive, watchEffect } from 'vue'
import { tabsKey, type TabsVariant } from './tabsContext'

// Reka Tabs with two looks (design-system §10): `underline` for page sections, `segmented` for a compact
// pill group. `v-model` is the active tab's value. Panels are optional: a page may switch its own content
// with v-if and use only the list.
const props = withDefaults(defineProps<{ variant?: TabsVariant }>(), { variant: 'underline' })
const model = defineModel<string>()

// Reka activates a tab on mousedown or focus; a trigger also selects on click, so a keyboard or a
// synthetic click behaves the same.
const context = reactive({
  variant: props.variant,
  select: (value: string) => {
    if (value !== model.value) model.value = value
  },
})
watchEffect(() => (context.variant = props.variant))
provide(tabsKey, context)
</script>

<template>
  <TabsRoot v-model="model"><slot /></TabsRoot>
</template>
