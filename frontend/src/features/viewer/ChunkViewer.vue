<script setup lang="ts">
import SafeHtml from '@/components/common/SafeHtml.vue'
import { renderMarkdown } from '@/features/chat/markdown'
import type { Chunk } from '@/features/documents/api'

// DOCX, MD and XLSX sources (SPEC-07 §5.4): the cited chunk with its heading path, and its
// neighbours for context. Chunk text is Markdown (tables included), sanitized by SafeHtml.
defineProps<{ chunks: Chunk[]; chunkId: string }>()
</script>

<template>
  <ol class="flex flex-col gap-3" data-testid="chunk-viewer">
    <li
      v-for="chunk in chunks"
      :key="chunk.id"
      :class="[
        'rounded-lg border px-4 py-3',
        chunk.id === chunkId ? 'border-brand bg-surface-selected' : 'bg-surface-sunken text-ink-muted',
      ]"
      :aria-current="chunk.id === chunkId ? 'true' : undefined"
    >
      <p class="mb-1 text-caption font-medium text-ink-muted">{{ chunk.headingPath.join(' › ') }}</p>
      <SafeHtml :html="renderMarkdown(chunk.text)" class="answer-prose" />
    </li>
  </ol>
</template>
