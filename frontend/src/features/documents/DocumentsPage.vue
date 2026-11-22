<script setup lang="ts">
import { FileText, Search } from 'lucide-vue-next'
import { onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PageContainer from '@/components/common/PageContainer.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { Banner } from '@/components/ui/banner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { SkeletonRows } from '@/components/ui/skeleton'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useUserStore } from '@/stores/user'
import type { Document, DocumentPatch } from './api'
import DocumentMetaDialog from './components/DocumentMetaDialog.vue'
import DocumentsTable from './components/DocumentsTable.vue'
import UploadPanel from './components/UploadPanel.vue'
import { useDocumentsStore, type DocumentFilter } from './store'

const store = useDocumentsStore()
const user = useUserStore()
const router = useRouter()

const editing = ref<Document | null>(null)
const editOpen = ref(false)
const deleting = ref<Document | null>(null)
const deleteOpen = ref(false)

// Documents are loaded once a demo user is chosen (every request needs X-Demo-User), and again for each new
// user, because a different user sees different documents (SPEC-07 §8).
watch(
  () => user.userId,
  (id, previous) => {
    if (!id) return
    if (previous) store.reset()
    void store.load()
  },
  { immediate: true },
)
onBeforeUnmount(() => store.stop())

const filters: { value: DocumentFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'current', label: 'Current' },
  { value: 'superseded', label: 'Superseded' },
  { value: 'failed', label: 'Failed' },
]

function edit(doc: Document) {
  editing.value = doc
  editOpen.value = true
}

async function saveEdit(changes: DocumentPatch) {
  if (editing.value) await store.patch(editing.value.id, changes)
}

async function toggleStatus(doc: Document) {
  const status = doc.status === 'current' ? 'superseded' : 'current'
  try {
    await store.patch(doc.id, { status })
    toast.success(status === 'superseded' ? 'Marked as superseded.' : 'Marked as current.')
  } catch {
    // The API client already showed the error.
  }
}

async function reingest(doc: Document) {
  try {
    await store.reingest(doc.id)
    toast.success(`Queued "${doc.title}" for ingestion.`)
  } catch {
    // The API client already showed the error.
  }
}

function askDelete(doc: Document) {
  deleting.value = doc
  deleteOpen.value = true
}

async function confirmDelete() {
  const doc = deleting.value
  if (!doc) return
  try {
    await store.remove(doc.id)
    toast.success(`Deleted "${doc.title}".`)
  } catch {
    // The API client already showed the error.
  }
}
</script>

<template>
  <PageContainer width="wide">
    <PageHeader title="Documents" description="Upload company documents and follow their ingestion." />

    <UploadPanel />

    <div class="flex flex-wrap items-center justify-between gap-3">
      <Tabs v-model="store.filter" variant="segmented">
        <TabsList aria-label="Filter documents">
          <TabsTrigger v-for="f in filters" :key="f.value" :value="f.value">{{ f.label }}</TabsTrigger>
        </TabsList>
      </Tabs>
      <label class="relative w-full sm:w-64">
        <span class="sr-only">Search by title</span>
        <Search
          class="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-ink-muted"
          aria-hidden="true"
        />
        <Input v-model="store.search" class="pl-9" placeholder="Search by title" />
      </label>
    </div>

    <SkeletonRows v-if="store.loading && !store.loaded" :rows="5" :cols="6" label="Loading documents…" />
    <Banner v-else-if="store.error && !store.loaded" tone="danger">
      {{ store.error }}
      <template #action>
        <Button size="sm" @click="store.load()">Try again</Button>
      </template>
    </Banner>
    <EmptyState
      v-else-if="store.items.length === 0"
      :icon="FileText"
      title="No documents yet"
      description="Drop files above to add the first one. Each document is read in the background and shows Ready when it can be searched."
    />
    <EmptyState
      v-else-if="store.visible.length === 0"
      :icon="Search"
      title="No documents match"
      description="Change the filter or the search to see more."
    />
    <DocumentsTable
      v-else
      :documents="store.visible"
      @open="(d) => router.push({ name: 'document', params: { id: d.id } })"
      @edit="edit"
      @reingest="reingest"
      @toggle-status="toggleStatus"
      @remove="askDelete"
    />

    <DocumentMetaDialog v-model:open="editOpen" :document="editing" :save="saveEdit" />
    <ConfirmDialog
      v-model:open="deleteOpen"
      title="Delete this document?"
      :description="`“${deleting?.title ?? ''}” and its searchable text will be removed. This cannot be undone.`"
      confirm-label="Delete document"
      danger
      @confirm="confirmDelete"
    />
  </PageContainer>
</template>
