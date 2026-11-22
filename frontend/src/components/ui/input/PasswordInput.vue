<script setup lang="ts">
import { Eye, EyeOff } from 'lucide-vue-next'
import { computed, useAttrs } from 'vue'
import Input from './Input.vue'

// A password field with an eye button that shows or hides what was typed. Every attribute (id, name,
// autocomplete, aria-invalid, class, the vee-validate handlers) goes to the input, so call sites read
// like a plain <Input>, minus `type`.
defineOptions({ inheritAttrs: false })
const model = defineModel<string>()
const attrs = useAttrs()
// `v-model:visible` lets a parent show the text, for example after it made the password for the user.
const visible = defineModel<boolean>('visible', { default: false })
const disabled = computed(() => attrs.disabled !== undefined && attrs.disabled !== false)
</script>

<template>
  <div class="relative">
    <Input v-bind="attrs" v-model="model" :type="visible ? 'text' : 'password'" class="pr-10" />
    <button
      type="button"
      class="absolute inset-y-0 right-0 flex w-9 items-center justify-center rounded-sm text-ink-muted hover:text-ink focus-visible:-outline-offset-2 disabled:opacity-50"
      :aria-label="visible ? 'Hide password' : 'Show password'"
      :aria-pressed="visible"
      :title="visible ? 'Hide password' : 'Show password'"
      :disabled="disabled"
      @click="visible = !visible"
    >
      <EyeOff v-if="visible" class="size-4" aria-hidden="true" />
      <Eye v-else class="size-4" aria-hidden="true" />
    </button>
  </div>
</template>
