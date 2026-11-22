<script setup lang="ts">
import { RotateCw } from 'lucide-vue-next'
import { computed } from 'vue'
import SafeHtml from '@/components/common/SafeHtml.vue'
import { Banner } from '@/components/ui/banner'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { renderAnswer, renderMarkdown } from '../markdown'
import type { ChatMessage } from '../store'
import SourceList from './SourceList.vue'

// One answer (SPEC-07 §5.3, §5.5). Citation buttons live inside v-html, so clicks are handled by
// delegation on this container (`data-cite`), not by Vue bindings.
const props = defineProps<{ message: ChatMessage; activeN?: number | null }>()
const emit = defineEmits<{ cite: [n: number]; retry: [] }>()

const html = computed(() => renderAnswer(props.message.answer, props.message.sources))
const streaming = computed(() => props.message.status === 'streaming')
const notFound = computed(() => props.message.status === 'done' && !props.message.found)
const error = computed(() => (props.message.status === 'error' ? props.message.error : null))
// quota_exhausted is not retryable until the plan is topped up (SPEC-07 §5.5).
const canRetry = computed(() => error.value?.code !== 'quota_exhausted')
const caption = computed(() => {
  const m = props.message
  if (m.status !== 'done' || !m.model) return ''
  return `${m.model}${m.latencyMs != null ? ` · ${(m.latencyMs / 1000).toFixed(1)} s` : ''}`
})
const showSources = computed(() => props.message.status !== 'error' && !notFound.value)

// SPEC-07 §9: the answer is announced once, when it settles, never per delta. The visible answer
// is not a live region (aria-busy is not honoured by every screen reader); this hidden one stays
// empty while streaming and gets plain text (no citation numbers) once the answer settles.
const CITES = /[^\S\n]*(?:\[\d+(?:\s*,\s*\d+)*\])+/g
const announcement = computed(() => {
  const m = props.message
  if (m.status === 'streaming') return ''
  // A danger Banner announces itself (role=alert); the quota warning does not.
  if (m.status === 'error') return error.value?.code === 'quota_exhausted' ? error.value.detail : ''
  if (m.status === 'stopped') return 'Stopped.'
  if (notFound.value) return m.answer
  const doc = new DOMParser().parseFromString(renderMarkdown(m.answer.replace(CITES, '')), 'text/html')
  return (doc.body.textContent ?? '').replace(/\s+/g, ' ').trim()
})

function onClick(event: MouseEvent) {
  const button = (event.target as HTMLElement | null)?.closest<HTMLElement>('button.citation')
  const n = Number(button?.dataset.cite)
  if (n > 0) emit('cite', n)
}
</script>

<template>
  <div class="flex flex-col gap-3" data-testid="answer">
    <div v-if="streaming && !message.answer" class="flex flex-col gap-2" role="status">
      <span class="sr-only">Searching the documents…</span>
      <Skeleton class="h-4 w-3/4" />
      <Skeleton class="h-4 w-1/2" />
    </div>

    <Banner v-if="notFound" tone="info" data-testid="not-found">
      {{ message.answer }}
    </Banner>
    <div v-else-if="message.answer" :aria-busy="streaming" @click="onClick">
      <SafeHtml :html="html" class="answer-prose" />
    </div>

    <p v-if="message.status === 'stopped'" class="text-caption text-ink-muted">Stopped.</p>

    <Banner v-if="error" :tone="error.code === 'quota_exhausted' ? 'warning' : 'danger'">
      {{ error.detail }}
      <template v-if="canRetry" #action>
        <Button size="sm" @click="emit('retry')"><RotateCw /> Retry</Button>
      </template>
    </Banner>

    <SourceList
      v-if="showSources"
      :sources="message.sources"
      :cited="message.cited"
      :active-n="activeN"
      @open="emit('cite', $event)"
    />

    <p v-if="caption" class="text-caption text-ink-muted">{{ caption }}</p>

    <p class="sr-only" aria-live="polite" data-testid="answer-live">{{ announcement }}</p>
  </div>
</template>
