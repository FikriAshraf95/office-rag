<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { applyFieldErrors } from '@/api/http'
import { Button } from '@/components/ui/button'
import { Dialog, DialogBody, DialogContent, DialogFooter, DialogHeader } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { useUserStore } from '@/stores/user'
import type { Document, DocumentPatch } from '../api'

// Edit a document's metadata and access groups (SPEC-08 §4.3). Sends only the fields that changed.
// `save` performs the PATCH and rejects when the API refuses; the dialog then shows the field errors and stays open.
const props = defineProps<{ document: Document | null; save: (changes: DocumentPatch) => Promise<unknown> }>()
const open = defineModel<boolean>('open', { default: false })

const user = useUserStore()
const form = reactive({
  title: '',
  docType: 'other',
  department: '',
  effectiveDate: '',
  version: '',
  accessGroups: [] as string[],
})
const errors = ref<Record<string, string>>({})
const saving = ref(false)

watch(
  () => [props.document, open.value] as const,
  ([doc, isOpen]) => {
    if (!doc || !isOpen) return
    form.title = doc.title
    form.docType = doc.docType
    form.department = doc.department ?? ''
    form.effectiveDate = doc.effectiveDate ?? ''
    form.version = doc.version ?? ''
    form.accessGroups = [...doc.accessGroups]
    errors.value = {}
  },
  { immediate: true },
)

// Groups the caller may use (SPEC-09 §3), plus any the document already has so none is dropped silently.
function groupChoices(): string[] {
  return [...new Set([...(user.current?.groups ?? []), ...form.accessGroups])]
}

function toggleGroup(group: string, on: boolean) {
  const next = new Set(form.accessGroups)
  if (on) next.add(group)
  else next.delete(group)
  form.accessGroups = groupChoices().filter((g) => next.has(g))
}

function changes(doc: Document): DocumentPatch {
  const out: DocumentPatch = {}
  if (form.title.trim() !== doc.title) out.title = form.title.trim()
  if (form.docType !== doc.docType) out.docType = form.docType
  if ((form.department.trim() || null) !== doc.department) out.department = form.department.trim() || null
  if ((form.effectiveDate || null) !== doc.effectiveDate) out.effectiveDate = form.effectiveDate || null
  if ((form.version.trim() || null) !== doc.version) out.version = form.version.trim() || null
  const same =
    form.accessGroups.length === doc.accessGroups.length &&
    form.accessGroups.every((g) => doc.accessGroups.includes(g))
  if (!same) out.accessGroups = form.accessGroups
  return out
}

async function submit() {
  const doc = props.document
  if (!doc) return
  const patch = changes(doc)
  if (Object.keys(patch).length === 0) {
    open.value = false
    return
  }
  saving.value = true
  errors.value = {}
  try {
    await props.save(patch)
    open.value = false
  } catch (e) {
    applyFieldErrors(e, (mapped) => (errors.value = mapped))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Dialog v-model:open="open">
    <DialogContent>
      <DialogHeader
        title="Edit details"
        description="Changes to status and access apply to search right away."
      />
      <DialogBody>
        <form id="document-meta-form" class="grid gap-3 sm:grid-cols-2" @submit.prevent="submit">
          <label class="flex flex-col gap-1 text-caption text-ink-muted sm:col-span-2">
            Title
            <Input v-model="form.title" :aria-invalid="!!errors.title || undefined" />
            <span v-if="errors.title" class="text-danger" role="alert">{{ errors.title }}</span>
          </label>
          <label class="flex flex-col gap-1 text-caption text-ink-muted">
            Document type
            <Select v-model="form.docType" aria-label="Document type">
              <option v-for="t in user.config?.docTypes ?? []" :key="t" :value="t">{{ t }}</option>
            </Select>
          </label>
          <label class="flex flex-col gap-1 text-caption text-ink-muted">
            Department
            <Input v-model="form.department" />
          </label>
          <label class="flex flex-col gap-1 text-caption text-ink-muted">
            Effective date
            <input
              v-model="form.effectiveDate"
              type="date"
              class="h-(--control-h) w-full rounded-md border border-border-input bg-surface px-3 text-body text-ink"
            />
            <span v-if="errors.effectiveDate" class="text-danger" role="alert">{{
              errors.effectiveDate
            }}</span>
          </label>
          <label class="flex flex-col gap-1 text-caption text-ink-muted">
            Version
            <Input v-model="form.version" />
          </label>
          <fieldset class="sm:col-span-2">
            <legend class="text-caption text-ink-muted">Who can see it</legend>
            <div class="mt-1 flex flex-wrap gap-x-4 gap-y-1">
              <label
                v-for="g in groupChoices()"
                :key="g"
                class="inline-flex items-center gap-2 text-body text-ink"
              >
                <input
                  type="checkbox"
                  class="size-4 accent-brand"
                  :checked="form.accessGroups.includes(g)"
                  @change="toggleGroup(g, ($event.target as HTMLInputElement).checked)"
                />
                {{ g }}
              </label>
            </div>
            <span v-if="errors.accessGroups" class="text-caption text-danger" role="alert">{{
              errors.accessGroups
            }}</span>
          </fieldset>
        </form>
      </DialogBody>
      <DialogFooter>
        <Button type="button" variant="secondary" @click="open = false">Cancel</Button>
        <Button
          type="submit"
          form="document-meta-form"
          variant="primary"
          :disabled="saving || !form.title.trim()"
        >
          Save changes
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
