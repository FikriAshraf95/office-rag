import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { isProblem, toProblem } from '@/api/http'
import { documentsApi, type Document, type DocumentPatch, type UploadDetails } from './api'

/** The list is refreshed this often while any row is queued or processing (SPEC-07 §6.2). */
export const POLL_INTERVAL_MS = 3000

export type UploadState = 'waiting' | 'uploading' | 'done' | 'duplicate' | 'error'

export interface UploadItem {
  key: number
  name: string
  state: UploadState
  /** 0–1 while uploading. */
  progress: number
  message?: string
  /** The document that was created, or the existing one for a duplicate the caller may see. */
  documentId?: string
  /** `duplicate_document` only: the existing document's title, when the caller can see it. */
  existingTitle?: string
}

export type DocumentFilter = 'all' | 'current' | 'superseded' | 'failed'

export const isActive = (d: Document) => d.ingestStatus === 'queued' || d.ingestStatus === 'processing'

export const useDocumentsStore = defineStore('documents', () => {
  const items = ref<Document[]>([])
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref<string | null>(null)
  const uploads = ref<UploadItem[]>([])
  const filter = ref<DocumentFilter>('all')
  const search = ref('')

  let timer: ReturnType<typeof setTimeout> | undefined
  let watching = false
  let nextKey = 1

  const visible = computed(() => {
    const term = search.value.trim().toLowerCase()
    return items.value.filter((d) => {
      if (filter.value === 'current' && d.status !== 'current') return false
      if (filter.value === 'superseded' && d.status !== 'superseded') return false
      if (filter.value === 'failed' && d.ingestStatus !== 'failed') return false
      return !term || d.title.toLowerCase().includes(term)
    })
  })
  const uploading = computed(() =>
    uploads.value.some((u) => u.state === 'waiting' || u.state === 'uploading'),
  )

  function clearTimer() {
    if (timer !== undefined) clearTimeout(timer)
    timer = undefined
  }

  /** Polls only while some row is queued or processing; each refresh decides whether to go on. */
  function schedule() {
    clearTimer()
    if (watching && items.value.some(isActive)) timer = setTimeout(() => void refresh(), POLL_INTERVAL_MS)
  }

  async function refresh() {
    try {
      items.value = await documentsApi.list()
      error.value = null
    } catch (e) {
      error.value = toProblem(e).detail
    } finally {
      loaded.value = true
      schedule()
    }
  }

  /** Loads the list and starts watching it. Call `stop()` when the page goes away. */
  async function load() {
    watching = true
    loading.value = !loaded.value
    try {
      await refresh()
    } finally {
      loading.value = false
    }
  }

  function stop() {
    watching = false
    clearTimer()
  }

  function reset() {
    stop()
    items.value = []
    loaded.value = false
    error.value = null
    uploads.value = []
  }

  /** Uploads the files one after another; the list refreshes after each so rows appear as they land. */
  async function uploadFiles(files: File[], details: UploadDetails) {
    const batch: UploadItem[] = files.map((f) => ({
      key: nextKey++,
      name: f.name,
      state: 'waiting',
      progress: 0,
    }))
    uploads.value = [...batch, ...uploads.value.filter((u) => u.state !== 'done')]
    for (const [i, file] of files.entries()) {
      const item = uploads.value.find((u) => u.key === batch[i]?.key)
      if (!item) continue
      item.state = 'uploading'
      try {
        const doc = await documentsApi.upload(
          file,
          { ...details, title: files.length === 1 ? details.title : undefined },
          (fraction) => (item.progress = fraction),
        )
        item.state = 'done'
        item.progress = 1
        item.documentId = doc.id
        await refresh()
      } catch (e) {
        const problem = toProblem(e)
        if (isProblem(e, 409, 'duplicate_document')) {
          item.state = 'duplicate'
          item.documentId = problem.existingId
          item.existingTitle = existingTitle(problem.existingId) ?? existingTitleFromDetail(problem.detail)
          item.message = problem.detail
        } else {
          item.state = 'error'
          item.message = fieldMessage(problem) ?? problem.detail
        }
      }
    }
  }

  function dismissUpload(key: number) {
    uploads.value = uploads.value.filter((u) => u.key !== key)
  }

  function existingTitle(id: string | undefined): string | undefined {
    return id ? items.value.find((d) => d.id === id)?.title : undefined
  }

  /** The API names the title in the detail: `This file is already uploaded as "Title".` */
  function existingTitleFromDetail(detail: string): string | undefined {
    return /"(.+)"/.exec(detail)?.[1]
  }

  function fieldMessage(problem: ReturnType<typeof toProblem>): string | undefined {
    const first = problem.errors ? Object.values(problem.errors)[0]?.[0] : undefined
    return first
  }

  function replace(doc: Document) {
    items.value = items.value.map((d) => (d.id === doc.id ? doc : d))
  }

  async function patch(id: string, changes: DocumentPatch): Promise<Document> {
    const doc = await documentsApi.patch(id, changes)
    replace(doc)
    return doc
  }

  /** Queues ingestion again; the row shows Queued at once and polling picks the progress up. */
  async function reingest(id: string): Promise<Document> {
    const doc = await documentsApi.reingest(id)
    replace(doc)
    schedule()
    return doc
  }

  async function remove(id: string) {
    await documentsApi.remove(id)
    items.value = items.value.filter((d) => d.id !== id)
  }

  return {
    items,
    loading,
    loaded,
    error,
    uploads,
    filter,
    search,
    visible,
    uploading,
    load,
    refresh,
    stop,
    reset,
    uploadFiles,
    dismissUpload,
    patch,
    reingest,
    remove,
  }
})
