<script setup lang="ts">
import { ChevronDown, ChevronRight, FileSearch } from 'lucide-vue-next'
import { ref, watch } from 'vue'
import { toProblem } from '@/api/http'
import EmptyState from '@/components/common/EmptyState.vue'
import { Banner } from '@/components/ui/banner'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { documentsApi, type Chunk } from '../api'

// SPEC-07 §6.3: ordinal, type, heading path, page or sheet, tokens and the text, expandable. Model-free text
// is rendered as plain text (interpolation), never as HTML.
const props = defineProps<{ documentId: string; chunkCount: number; version: number }>()

const PAGE_SIZE = 50
const items = ref<Chunk[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)
const open = ref(new Set<string>())

async function load(reset: boolean) {
  loading.value = true
  error.value = null
  try {
    const page = await documentsApi.chunks(props.documentId, reset ? 0 : items.value.length, PAGE_SIZE)
    items.value = reset ? page.items : [...items.value, ...page.items]
    total.value = page.total
    if (reset) open.value = new Set()
  } catch (e) {
    error.value = toProblem(e).detail
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.documentId, props.version, props.chunkCount],
  () => void load(true),
  { immediate: true },
)

function toggle(id: string) {
  const next = new Set(open.value)
  if (!next.delete(id)) next.add(id)
  open.value = next
}

function where(chunk: Chunk): string {
  if (chunk.sheet) return `Sheet ${chunk.sheet}`
  if (chunk.pageStart == null) return '–'
  return chunk.pageEnd && chunk.pageEnd !== chunk.pageStart
    ? `Pages ${chunk.pageStart}–${chunk.pageEnd}`
    : `Page ${chunk.pageStart}`
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div v-if="loading && !items.length" class="flex flex-col gap-2" role="status">
      <span class="sr-only">Loading chunks…</span>
      <Skeleton v-for="n in 4" :key="n" class="h-12 w-full" />
    </div>
    <Banner v-else-if="error" tone="danger">{{ error }}</Banner>
    <EmptyState
      v-else-if="!items.length"
      :icon="FileSearch"
      title="No chunks yet"
      description="The text appears here once ingestion finishes."
    />
    <template v-else>
      <p class="text-caption text-ink-muted">{{ total }} chunks</p>
      <ol class="flex flex-col divide-y rounded-lg border bg-surface" data-testid="chunks-list">
        <li v-for="chunk in items" :key="chunk.id">
          <button
            type="button"
            class="flex w-full items-start gap-2 px-3 py-2.5 text-left hover:bg-surface-hover"
            :aria-expanded="open.has(chunk.id)"
            @click="toggle(chunk.id)"
          >
            <component
              :is="open.has(chunk.id) ? ChevronDown : ChevronRight"
              class="mt-1 size-4 shrink-0 text-ink-muted"
              aria-hidden="true"
            />
            <span class="w-8 shrink-0 text-caption text-ink-muted">#{{ chunk.ordinal + 1 }}</span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-body-strong text-ink">{{
                chunk.headingPath.join(' › ')
              }}</span>
              <span class="block text-caption text-ink-muted">
                {{ chunk.chunkType }} · {{ where(chunk) }} · {{ chunk.tokenCount }} tokens
              </span>
            </span>
          </button>
          <pre
            v-if="open.has(chunk.id)"
            class="overflow-x-auto border-t bg-surface-sunken px-4 py-3 text-body whitespace-pre-wrap text-ink"
            >{{ chunk.text }}</pre>
        </li>
      </ol>
      <Button v-if="items.length < total" :disabled="loading" @click="load(false)">Show more</Button>
    </template>
  </div>
</template>
