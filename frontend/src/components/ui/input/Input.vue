<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { fieldClass } from '.'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
const model = defineModel<string>()
</script>

<template>
  <input v-model="model" :class="cn(fieldClass, 'h-(--control-h) w-full px-3', props.class)" />
</template>
