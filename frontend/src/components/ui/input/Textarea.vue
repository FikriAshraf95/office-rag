<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { fieldClass } from '.'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
const model = defineModel<string>()
</script>

<template>
  <textarea v-model="model" :class="cn(fieldClass, 'block w-full px-3 py-2', props.class)" />
</template>
