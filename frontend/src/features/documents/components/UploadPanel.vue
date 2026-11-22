<script setup lang="ts">
import { AlertCircle, CheckCircle2, ChevronDown, ChevronRight, Loader2, X } from 'lucide-vue-next'
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import FileDrop from '@/components/common/FileDrop.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { useUserStore } from '@/stores/user'
import { useDocumentsStore, type UploadItem } from '../store'

// SPEC-07 §6.1: a multi-file drop zone, optional details applied to the whole batch, and one result row per file.
const user = useUserStore()
const documents = useDocumentsStore()

const accept = computed(() => user.config?.allowedExtensions.join(',') ?? '')
const maxBytes = computed(() => user.config?.maxUploadBytes)
const docTypes = computed(() => user.config?.docTypes ?? [])
// Uploads may only use the caller's own groups (SPEC-09 §3).
const myGroups = computed(() => user.current?.groups ?? [])

const showDetails = ref(false)
const pending = ref<File[]>([])
const details = reactive({ title: '', docType: '', department: '', effectiveDate: '', accessGroups: ['all'] })

watch(
  myGroups,
  (groups) => {
    details.accessGroups = groups.includes('all') ? ['all'] : groups.slice(0, 1)
  },
  { immediate: true },
)

function toggleGroup(group: string, on: boolean) {
  const next = new Set(details.accessGroups)
  if (on) next.add(group)
  else next.delete(group)
  details.accessGroups = myGroups.value.filter((g) => next.has(g))
}

async function start(files: File[]) {
  pending.value = files
  await send()
}

async function send() {
  const files = pending.value
  pending.value = []
  await documents.uploadFiles(files, {
    title: details.title.trim(),
    docType: details.docType,
    department: details.department.trim(),
    effectiveDate: details.effectiveDate,
    accessGroups: details.accessGroups,
  })
  details.title = ''
}

const overall = computed(() => {
  const active = documents.uploads.find((u) => u.state === 'uploading')
  return documents.uploading ? (active?.progress ?? 0) : null
})

function summary(item: UploadItem): string {
  switch (item.state) {
    case 'waiting':
      return 'Waiting'
    case 'uploading':
      return `Uploading ${Math.round(item.progress * 100)}%`
    case 'done':
      return 'Uploaded. Ingestion is queued.'
    case 'duplicate':
      return item.existingTitle ? 'Already uploaded as' : 'Already uploaded'
    default:
      return item.message ?? 'The upload failed. Try again.'
  }
}
</script>

<template>
  <section class="flex flex-col gap-3 rounded-lg border bg-surface p-4" aria-label="Upload documents">
    <FileDrop
      :accept="accept"
      :max-bytes="maxBytes"
      :progress="overall"
      label="Drop files here, or choose them"
      hint="PDF, DOCX, XLSX, Markdown, PNG or JPG"
      @files="start"
    />

    <div>
      <button
        type="button"
        class="inline-flex items-center gap-1 text-body-strong text-ink-muted hover:text-ink"
        :aria-expanded="showDetails"
        aria-controls="upload-details"
        @click="showDetails = !showDetails"
      >
        <component :is="showDetails ? ChevronDown : ChevronRight" class="size-4" aria-hidden="true" />
        Details for the next upload
      </button>
      <div v-if="showDetails" id="upload-details" class="mt-3 grid gap-3 sm:grid-cols-2">
        <label class="flex flex-col gap-1 text-caption text-ink-muted">
          Title (one file only)
          <Input v-model="details.title" placeholder="Taken from the file when empty" />
        </label>
        <label class="flex flex-col gap-1 text-caption text-ink-muted">
          Document type
          <Select v-model="details.docType" aria-label="Document type">
            <option value="">Detect from the file</option>
            <option v-for="t in docTypes" :key="t" :value="t">{{ t }}</option>
          </Select>
        </label>
        <label class="flex flex-col gap-1 text-caption text-ink-muted">
          Department
          <Input v-model="details.department" placeholder="For example HR, Finance, IT" />
        </label>
        <label class="flex flex-col gap-1 text-caption text-ink-muted">
          Effective date
          <input
            v-model="details.effectiveDate"
            type="date"
            class="h-(--control-h) w-full rounded-md border border-border-input bg-surface px-3 text-body text-ink"
          />
        </label>
        <fieldset class="sm:col-span-2">
          <legend class="text-caption text-ink-muted">Who can see it</legend>
          <div class="mt-1 flex flex-wrap gap-x-4 gap-y-1">
            <label v-for="g in myGroups" :key="g" class="inline-flex items-center gap-2 text-body text-ink">
              <input
                type="checkbox"
                class="size-4 accent-brand"
                :checked="details.accessGroups.includes(g)"
                @change="toggleGroup(g, ($event.target as HTMLInputElement).checked)"
              />
              {{ g }}
            </label>
          </div>
          <p v-if="details.accessGroups.length === 0" class="mt-1 text-caption text-danger" role="alert">
            Choose at least one group.
          </p>
        </fieldset>
      </div>
    </div>

    <ul v-if="documents.uploads.length" class="flex flex-col gap-1.5" aria-label="Upload results">
      <li
        v-for="item in documents.uploads"
        :key="item.key"
        class="flex items-center gap-2 rounded-md bg-surface-sunken px-3 py-2 text-body"
        :data-state="item.state"
      >
        <Loader2
          v-if="item.state === 'uploading' || item.state === 'waiting'"
          class="size-4 shrink-0 animate-spin text-ink-muted"
          aria-hidden="true"
        />
        <CheckCircle2
          v-else-if="item.state === 'done'"
          class="size-4 shrink-0 text-success"
          aria-hidden="true"
        />
        <AlertCircle
          v-else
          class="size-4 shrink-0"
          :class="item.state === 'duplicate' ? 'text-warning' : 'text-danger'"
          aria-hidden="true"
        />
        <span class="min-w-0 flex-1">
          <span class="text-body-strong text-ink">{{ item.name }}</span>
          <span class="text-ink-muted"> · {{ summary(item) }}</span>
          <template v-if="item.state === 'duplicate' && item.existingTitle">
            <RouterLink
              v-if="item.documentId"
              :to="{ name: 'document', params: { id: item.documentId } }"
              class="ml-1 text-brand-ink hover:underline"
              >{{ item.existingTitle }}</RouterLink
            >
            <em v-else class="ml-1">{{ item.existingTitle }}</em>
          </template>
        </span>
        <Button
          variant="ghost"
          size="icon"
          :aria-label="`Dismiss ${item.name}`"
          :disabled="item.state === 'uploading' || item.state === 'waiting'"
          @click="documents.dismissUpload(item.key)"
        >
          <X />
        </Button>
      </li>
    </ul>
  </section>
</template>
