<script setup lang="ts">
import { computed } from 'vue'
import { sanitizeAnswer } from '@/lib/sanitize'

// The only place model or user HTML is rendered (SPEC-07 §3). Answers come from markdown-it with
// `html: false`; this is defence in depth with the answer allowlist. ESLint bans v-html elsewhere.
const props = defineProps<{ html: string | null | undefined; inline?: boolean }>()
const clean = computed(() => sanitizeAnswer(props.html ?? ''))
</script>

<template>
  <span v-if="inline" v-html="clean" />
  <div v-else v-html="clean" />
</template>
