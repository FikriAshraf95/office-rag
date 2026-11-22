<script setup lang="ts">
import { ArrowLeft, Download, ExternalLink, X } from 'lucide-vue-next'
import { computed, defineAsyncComponent, ref, watch } from 'vue'
import { toProblem } from '@/api/http'
import SafeHtml from '@/components/common/SafeHtml.vue'
import { Banner } from '@/components/ui/banner'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { StatusPill } from '@/components/ui/status-pill'
import type { Source } from '@/features/chat/api'
import { renderMarkdown } from '@/features/chat/markdown'
import { documentsApi, saveBlob, type Chunk, type Document } from '@/features/documents/api'
import { formatDate } from '@/lib/format'
import ChunkViewer from './ChunkViewer.vue'
import ImageViewer from './ImageViewer.vue'

// pdf.js is large: it loads only when a PDF source opens.
const PdfViewer = defineAsyncComponent(() => import('./PdfViewer.vue'))

// The cited source (SPEC-07 §5.4). Responsive per design-system §11: a side panel from 1280px
// (width 480–960, resizable), an overlay with a scrim below that, full screen with a back button
// on phones. Originals are fetched as Blobs through http.ts, which sends X-Demo-User.
const props = defineProps<{ source: Source }>()
const emit = defineEmits<{ close: [] }>()

const WIDTH_KEY = 'rag-source-panel-w'
const MIN_W = 480
const MAX_W = 960

function storedWidth(): number {
  try {
    const n = Number(localStorage.getItem(WIDTH_KEY))
    return n >= MIN_W && n <= MAX_W ? n : 600
  } catch {
    return 600
  }
}
const width = ref(storedWidth())

function startResize(event: PointerEvent) {
  const startX = event.clientX
  const startW = width.value
  const target = event.currentTarget as HTMLElement
  target.setPointerCapture(event.pointerId)
  const move = (e: PointerEvent) => {
    // The panel sits on the right, so dragging left widens it.
    width.value = Math.min(MAX_W, Math.max(MIN_W, startW + (startX - e.clientX)))
  }
  const up = () => {
    target.removeEventListener('pointermove', move)
    target.removeEventListener('pointerup', up)
    target.removeEventListener('pointercancel', up)
    try {
      localStorage.setItem(WIDTH_KEY, String(width.value))
    } catch {
      // Not persisted.
    }
  }
  target.addEventListener('pointermove', move)
  target.addEventListener('pointerup', up)
  target.addEventListener('pointercancel', up)
}

const document_ = ref<Document | null>(null)
const chunks = ref<Chunk[]>([])
const blob = ref<Blob | null>(null)
const loading = ref(true)
const fileError = ref<string | null>(null)

const kind = computed<'pdf' | 'image' | 'text'>(() => {
  const t = props.source.fileType
  if (t === 'pdf') return 'pdf'
  if (t === 'png' || t === 'jpg' || t === 'jpeg') return 'image'
  return 'text'
})

/** The cited chunk's text: from the API when it loaded, else the snippet the stream carried. */
const target = computed(() => chunks.value.find((c) => c.id === props.source.chunkId) ?? null)
const quote = computed(() => target.value?.text ?? props.source.snippet)
const textChunks = computed<Chunk[]>(() => {
  if (chunks.value.length) return chunks.value
  const s = props.source
  return [
    {
      id: s.chunkId,
      ordinal: 0,
      chunkType: 'text',
      text: s.snippet,
      headingPath: s.headingPath,
      section: s.section,
      pageStart: s.pageStart,
      pageEnd: s.pageEnd,
      sheet: s.sheet,
      tokenCount: 0,
    },
  ]
})

let run = 0
async function load() {
  const mine = ++run
  const s = props.source
  loading.value = true
  fileError.value = null
  document_.value = null
  chunks.value = []
  blob.value = null
  const wantsFile = kind.value !== 'text'
  const [doc, around, file] = await Promise.allSettled([
    documentsApi.get(s.documentId),
    documentsApi.chunksAround(s.documentId, s.chunkId, 1),
    wantsFile ? documentsApi.file(s.documentId) : Promise.resolve(null),
  ])
  if (mine !== run) return
  if (doc.status === 'fulfilled') document_.value = doc.value
  if (around.status === 'fulfilled') chunks.value = around.value
  if (file.status === 'fulfilled') blob.value = file.value
  else fileError.value = toProblem(file.reason).detail
  loading.value = false
}

watch(() => props.source.chunkId, load, { immediate: true })

const downloading = ref(false)
async function download() {
  downloading.value = true
  try {
    const file = blob.value ?? (await documentsApi.file(props.source.documentId))
    saveBlob(file, document_.value?.filename ?? props.source.title)
  } catch (e) {
    fileError.value = toProblem(e).detail
  } finally {
    downloading.value = false
  }
}

const meta = computed(() => {
  const date = document_.value?.effectiveDate ?? props.source.effectiveDate
  return date ? `Effective ${formatDate(date)}` : ''
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex justify-end xl:static xl:inset-auto xl:z-auto xl:block xl:shrink-0">
    <div class="absolute inset-0 bg-scrim xl:hidden" aria-hidden="true" @click="emit('close')" />
    <aside
      class="relative flex h-full w-full flex-col bg-surface shadow-lg sm:w-(--panel-w) sm:max-w-full xl:sticky xl:top-0 xl:h-[calc(100vh-9rem)] xl:rounded-lg xl:border xl:shadow-sm"
      :style="{ '--panel-w': `${width}px` }"
      aria-label="Source"
      data-testid="source-panel"
    >
      <div
        class="absolute inset-y-0 left-0 z-10 hidden w-1.5 cursor-col-resize xl:block"
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize panel"
        @pointerdown="startResize"
      />
      <header class="flex items-start gap-2 border-b px-4 py-3">
        <Button
          variant="ghost"
          size="icon"
          class="sm:hidden"
          aria-label="Back to the answer"
          @click="emit('close')"
        >
          <ArrowLeft />
        </Button>
        <div class="min-w-0 flex-1">
          <h2 class="truncate text-title text-ink">{{ source.title }}</h2>
          <div class="mt-1 flex flex-wrap items-center gap-2 text-caption text-ink-muted">
            <StatusPill
              v-if="document_"
              :color="document_.status === 'current' ? 'green' : 'grey'"
              :label="document_.status === 'current' ? 'Current' : 'Superseded'"
            />
            <span v-if="meta">{{ meta }}</span>
            <RouterLink
              :to="{ name: 'document', params: { id: source.documentId } }"
              class="inline-flex items-center gap-1 text-brand-ink hover:underline"
            >
              Open document <ExternalLink class="size-3.5" aria-hidden="true" />
            </RouterLink>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          class="max-sm:hidden"
          aria-label="Close source"
          @click="emit('close')"
        >
          <X />
        </Button>
      </header>

      <div class="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        <div v-if="loading" class="flex flex-col gap-2" role="status">
          <span class="sr-only">Loading the source…</span>
          <Skeleton class="h-16 w-full" />
          <Skeleton class="h-40 w-full" />
        </div>
        <div v-else class="flex flex-col gap-4">
          <Banner v-if="fileError" tone="warning">{{ fileError }}</Banner>

          <template v-if="kind === 'text'">
            <ChunkViewer :chunks="textChunks" :chunk-id="source.chunkId" />
          </template>
          <template v-else>
            <!-- PDF: the quote above the page; image: the extracted text below the image (§5.4). -->
            <ImageViewer v-if="kind === 'image' && blob" :blob="blob" :alt="source.title" />
            <blockquote
              class="rounded-lg border-l-4 border-brand bg-surface-selected px-4 py-3"
              data-testid="source-quote"
            >
              <SafeHtml :html="renderMarkdown(quote)" class="answer-prose" />
            </blockquote>
            <PdfViewer v-if="kind === 'pdf' && blob" :blob="blob" :page="source.pageStart ?? 1" />
          </template>
        </div>
      </div>

      <footer class="border-t px-4 py-3">
        <Button :disabled="downloading" @click="download"><Download /> Download original</Button>
      </footer>
    </aside>
  </div>
</template>
