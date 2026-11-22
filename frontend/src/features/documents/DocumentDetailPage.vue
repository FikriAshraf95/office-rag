<script setup lang="ts">
import { ArrowLeft, Download, FileQuestion, Upload } from 'lucide-vue-next'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { isProblem, toProblem } from '@/api/http'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PageContainer from '@/components/common/PageContainer.vue'
import { Badge } from '@/components/ui/badge'
import { Banner } from '@/components/ui/banner'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { StatusPill } from '@/components/ui/status-pill'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { formatDate, formatDateTime } from '@/lib/format'
import { formatBytes } from '@/lib/utils'
import { useUserStore } from '@/stores/user'
import { documentsApi, saveBlob, type Document, type DocumentPatch } from './api'
import { POLL_INTERVAL_MS } from './store'
import ChunksTab from './components/ChunksTab.vue'
import DocumentMetaDialog from './components/DocumentMetaDialog.vue'
import IngestStatusPill from './components/IngestStatusPill.vue'

// SPEC-07 §6.3: header, metadata, failed-ingestion banner with Retry, and the Chunks and Original tabs.
const route = useRoute()
const router = useRouter()
const user = useUserStore()

const doc = ref<Document | null>(null)
const loading = ref(true)
const notFound = ref(false)
const error = ref<string | null>(null)
const tab = ref('chunks')
const retrying = ref(false)
const replacing = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
/** Bumped when ingestion finishes so the Chunks tab reloads. */
const chunksVersion = ref(0)
const editOpen = ref(false)
const deleteOpen = ref(false)
let pollTimer: ReturnType<typeof setTimeout> | undefined

const imageUrl = ref<string | null>(null)
const fileError = ref<string | null>(null)
const isImage = computed(() => doc.value?.fileType === 'png' || doc.value?.fileType === 'jpg')

function revoke() {
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
  imageUrl.value = null
}

async function load(id: string) {
  loading.value = true
  notFound.value = false
  error.value = null
  revoke()
  try {
    doc.value = await documentsApi.get(id)
    // Opened while ingestion runs (e.g. straight after upload): keep watching until it settles.
    if (doc.value.ingestStatus === 'queued' || doc.value.ingestStatus === 'processing') watchIngestion(id)
    if (isImage.value) await showImage(doc.value.id)
  } catch (e) {
    doc.value = null
    if (isProblem(e, 404)) notFound.value = true
    else error.value = toProblem(e).detail
  } finally {
    loading.value = false
  }
}

// The file needs X-Demo-User, so it is fetched and shown from a blob, never linked directly (SPEC-07 §11 check 11).
async function showImage(id: string) {
  try {
    imageUrl.value = URL.createObjectURL(await documentsApi.file(id))
  } catch (e) {
    fileError.value = toProblem(e).detail
  }
}

watch(
  () => [route.params.id, user.userId],
  () => {
    if (typeof route.params.id === 'string') void load(route.params.id)
  },
  { immediate: true },
)
onBeforeUnmount(revoke)

async function download() {
  if (!doc.value) return
  try {
    saveBlob(await documentsApi.file(doc.value.id), doc.value.filename)
  } catch (e) {
    toast.error(toProblem(e).detail)
  }
}

async function patch(changes: DocumentPatch) {
  if (doc.value) doc.value = await documentsApi.patch(doc.value.id, changes)
}

async function toggleStatus() {
  if (!doc.value) return
  try {
    await patch({ status: doc.value.status === 'current' ? 'superseded' : 'current' })
  } catch {
    // The API client already showed the error.
  }
}

/** Queues ingestion again and watches the document until it settles (SPEC-03 §7). */
async function retry() {
  if (!doc.value) return
  retrying.value = true
  try {
    doc.value = await documentsApi.reingest(doc.value.id)
    watchIngestion(doc.value.id)
  } catch {
    // The API client already showed the error.
  } finally {
    retrying.value = false
  }
}

/** Replaces the stored file with a new version of this document and watches the re-ingest (SPEC-08 §4.8). */
async function replaceFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!doc.value || !file) return
  replacing.value = true
  try {
    doc.value = await documentsApi.replaceFile(doc.value.id, file)
    revoke()
    fileError.value = null
    watchIngestion(doc.value.id)
    toast.success('File replaced. Ingestion has started.')
  } catch {
    // The API client already showed the error.
  } finally {
    replacing.value = false
  }
}

function watchIngestion(id: string) {
  if (pollTimer !== undefined) clearTimeout(pollTimer)
  pollTimer = setTimeout(async () => {
    try {
      const fresh = await documentsApi.get(id)
      if (route.params.id !== id) return
      doc.value = fresh
      if (fresh.ingestStatus === 'queued' || fresh.ingestStatus === 'processing') watchIngestion(id)
      else chunksVersion.value += 1
    } catch {
      // The next navigation reloads the page.
    }
  }, POLL_INTERVAL_MS)
}
onBeforeUnmount(() => {
  if (pollTimer !== undefined) clearTimeout(pollTimer)
})

async function remove() {
  if (!doc.value) return
  try {
    await documentsApi.remove(doc.value.id)
    toast.success(`Deleted "${doc.value.title}".`)
    await router.push({ name: 'documents' })
  } catch {
    // The API client already showed the error.
  }
}

const rows = computed(() => {
  const d = doc.value
  if (!d) return []
  return [
    ['Type', d.docType],
    ['Department', d.department ?? '–'],
    ['Effective date', d.effectiveDate ? formatDate(d.effectiveDate) : '–'],
    ['Version', d.version ?? '–'],
    ['Language', d.language ?? '–'],
    ['Pages', d.pageCount?.toString() ?? '–'],
    ['Chunks', d.chunkCount.toString()],
    ['File', `${d.filename} · ${formatBytes(d.sizeBytes)}`],
    ['Uploaded', `${formatDateTime(d.createdAt)} by ${d.uploadedBy}`],
  ] as const
})
</script>

<template>
  <PageContainer width="wide">
    <RouterLink
      :to="{ name: 'documents' }"
      class="inline-flex items-center gap-1 text-body text-ink-muted hover:text-ink"
    >
      <ArrowLeft class="size-4" aria-hidden="true" /> All documents
    </RouterLink>

    <div v-if="loading" class="flex flex-col gap-3" role="status">
      <span class="sr-only">Loading document…</span>
      <Skeleton class="h-8 w-1/2" />
      <Skeleton class="h-40 w-full" />
    </div>
    <EmptyState
      v-else-if="notFound"
      :icon="FileQuestion"
      title="Document not found"
      description="It may have been deleted, or you may not have access to it."
    >
      <Button variant="primary" @click="router.push({ name: 'documents' })">Back to documents</Button>
    </EmptyState>
    <Banner v-else-if="error" tone="danger">{{ error }}</Banner>

    <template v-else-if="doc">
      <header class="flex flex-wrap items-start justify-between gap-4">
        <div class="min-w-0">
          <h1 class="text-display break-words text-ink">{{ doc.title }}</h1>
          <div class="mt-2 flex flex-wrap items-center gap-2">
            <StatusPill
              :color="doc.status === 'current' ? 'green' : 'grey'"
              :label="doc.status === 'current' ? 'Current' : 'Superseded'"
            />
            <IngestStatusPill :status="doc.ingestStatus" :error="doc.ingestError" />
            <Badge v-for="g in doc.accessGroups" :key="g">{{ g }}</Badge>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <template v-if="user.isAdmin">
            <Button @click="toggleStatus">{{
              doc.status === 'current' ? 'Mark superseded' : 'Mark current'
            }}</Button>
            <Button @click="editOpen = true">Edit details</Button>
            <input
              ref="fileInput"
              type="file"
              class="hidden"
              accept=".pdf,.docx,.xlsx,.md,.png,.jpg,.jpeg"
              @change="replaceFile"
            />
            <Button :disabled="replacing" @click="fileInput?.click()"><Upload /> Replace file</Button>
          </template>
          <Button variant="primary" @click="download"><Download /> Download original</Button>
          <Button v-if="user.isAdmin" variant="ghost" class="text-danger" @click="deleteOpen = true"
            >Delete</Button
          >
        </div>
      </header>

      <Banner v-if="doc.ingestStatus === 'failed'" tone="danger">
        {{ doc.ingestError ?? 'Ingestion failed. Select Retry to try again.' }}
        <template v-if="user.isAdmin" #action>
          <Button size="sm" :disabled="retrying" @click="retry">Retry</Button>
        </template>
      </Banner>

      <section v-if="doc.summary || doc.tags.length" aria-label="Summary" class="flex flex-col gap-2">
        <p v-if="doc.summary" class="text-body text-ink">{{ doc.summary }}</p>
        <div v-if="doc.tags.length" class="flex flex-wrap gap-2">
          <Badge v-for="t in doc.tags" :key="t">{{ t }}</Badge>
        </div>
      </section>

      <dl class="grid gap-x-8 gap-y-3 rounded-lg border bg-surface p-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="[label, value] in rows" :key="label" class="min-w-0">
          <dt class="text-caption text-ink-muted">{{ label }}</dt>
          <dd class="truncate text-body text-ink" :title="value">{{ value }}</dd>
        </div>
      </dl>

      <Tabs v-model="tab">
        <TabsList aria-label="Document sections">
          <TabsTrigger value="chunks">Chunks</TabsTrigger>
          <TabsTrigger value="original">Original</TabsTrigger>
        </TabsList>
        <TabsContent value="chunks" class="pt-4">
          <ChunksTab :document-id="doc.id" :chunk-count="doc.chunkCount" :version="chunksVersion" />
        </TabsContent>
        <TabsContent value="original" class="pt-4">
          <img
            v-if="imageUrl"
            :src="imageUrl"
            :alt="`Original file: ${doc.title}`"
            class="max-h-[70vh] max-w-full rounded-lg border"
          />
          <Banner v-else-if="fileError" tone="danger">{{ fileError }}</Banner>
          <p v-else-if="!isImage" class="text-body text-ink-muted">
            Download the original to open it. A built-in viewer for PDFs arrives with the source panel.
          </p>
        </TabsContent>
      </Tabs>

      <DocumentMetaDialog v-model:open="editOpen" :document="doc" :save="patch" />
      <ConfirmDialog
        v-model:open="deleteOpen"
        title="Delete this document?"
        :description="`“${doc.title}” and its searchable text will be removed. This cannot be undone.`"
        confirm-label="Delete document"
        danger
        @confirm="remove"
      />
    </template>
  </PageContainer>
</template>
