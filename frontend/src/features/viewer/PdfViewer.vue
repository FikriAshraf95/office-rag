<script setup lang="ts">
import * as pdfjs from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { Banner } from '@/components/ui/banner'
import { Skeleton } from '@/components/ui/skeleton'

// PDF sources (SPEC-07 §5.4): pdf.js renders the original (bytes from the Blob fetched with
// X-Demo-User) and scrolls to `page`. The worker comes through Vite's `?url`. Pages render in
// order up to a cap, which is plenty for the demo documents.
const props = defineProps<{ blob: Blob; page: number }>()

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl

const MAX_PAGES = 50
const SCALE = 1.25

const container = ref<HTMLElement | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const pageCount = ref(0)
let task: pdfjs.PDFDocumentLoadingTask | null = null
let run = 0

async function render() {
  const mine = ++run
  loading.value = true
  error.value = null
  await task?.destroy()
  task = null
  try {
    // pdf.js takes ownership of the buffer, so it gets a fresh copy each time.
    const data = new Uint8Array(await props.blob.arrayBuffer())
    const mineTask = pdfjs.getDocument({ data })
    task = mineTask
    const loaded = await mineTask.promise
    if (mine !== run) return
    pageCount.value = Math.min(loaded.numPages, MAX_PAGES)
    loading.value = false
    await nextTick()
    const host = container.value
    if (!host) return
    host.replaceChildren()
    for (let n = 1; n <= pageCount.value; n++) {
      const pdfPage = await loaded.getPage(n)
      if (mine !== run) return
      const viewport = pdfPage.getViewport({ scale: SCALE })
      const canvas = document.createElement('canvas')
      canvas.width = viewport.width
      canvas.height = viewport.height
      canvas.dataset.page = String(n)
      canvas.setAttribute('role', 'img')
      canvas.setAttribute('aria-label', `Page ${n}`)
      canvas.className = 'mx-auto mb-3 h-auto max-w-full rounded-sm border bg-surface shadow-sm'
      host.append(canvas)
      await pdfPage.render({ canvas, viewport }).promise
      if (n === props.page) canvas.scrollIntoView({ block: 'start' })
    }
  } catch {
    if (mine === run) {
      loading.value = false
      error.value = "This PDF can't be shown here. Download the original instead."
    }
  }
}

watch(() => props.blob, render, { immediate: true })
watch(
  () => props.page,
  () =>
    container.value?.querySelector(`canvas[data-page="${props.page}"]`)?.scrollIntoView({ block: 'start' }),
)
onBeforeUnmount(() => {
  run++
  void task?.destroy()
})
</script>

<template>
  <div data-testid="pdf-viewer" :data-page="page">
    <div v-if="loading" class="flex flex-col gap-2" role="status">
      <span class="sr-only">Loading the PDF…</span>
      <Skeleton class="h-64 w-full" />
    </div>
    <Banner v-else-if="error" tone="danger">{{ error }}</Banner>
    <div ref="container" :class="{ hidden: loading || error }" />
  </div>
</template>
