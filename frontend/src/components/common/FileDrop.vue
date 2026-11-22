<script setup lang="ts">
import { Upload } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { cn, formatBytes } from '@/lib/utils'

/**
 * Drop files here, or click to choose them (SPEC-07 §3: accepts several files, emits `files`). It
 * checks each file's size and browser-reported type before emitting, as a courtesy: the server
 * decides from the file's bytes. Accepted files are emitted together; refused ones are named in the
 * error. Keyboard users get a real button.
 */
const props = withDefaults(
  defineProps<{
    /** The input's `accept`, e.g. "image/png,image/jpeg". */
    accept?: string
    maxBytes?: number
    label?: string
    hint?: string
    disabled?: boolean
    /** 0–1 while uploading. */
    progress?: number | null
    compact?: boolean
  }>(),
  {
    accept: undefined,
    maxBytes: undefined,
    label: 'Drop files here, or choose them',
    hint: undefined,
    disabled: false,
    progress: null,
    compact: false,
  },
)
const emit = defineEmits<{ files: [files: File[]] }>()

const input = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const error = ref<string | null>(null)
const busy = computed(() => props.progress !== null)

function accepted(file: File): boolean {
  if (!props.accept) return true
  return props.accept.split(',').some((rule) => {
    const r = rule.trim().toLowerCase()
    if (r.startsWith('.')) return file.name.toLowerCase().endsWith(r)
    if (r.endsWith('/*')) return file.type.startsWith(r.slice(0, -1))
    return file.type === r
  })
}

function take(files: FileList | File[] | null | undefined) {
  error.value = null
  const list = Array.from(files ?? [])
  if (list.length === 0 || props.disabled || busy.value) return
  const ok: File[] = []
  const problems: string[] = []
  for (const file of list) {
    if (!accepted(file)) problems.push(`${file.name}: this type of file isn't allowed here.`)
    else if (props.maxBytes !== undefined && file.size > props.maxBytes)
      problems.push(`${file.name}: this file is too large. The limit is ${formatBytes(props.maxBytes)}.`)
    else ok.push(file)
  }
  if (problems.length) error.value = problems.join(' ')
  if (ok.length) emit('files', ok)
  if (input.value) input.value.value = ''
}

function onDrop(event: DragEvent) {
  dragging.value = false
  take(event.dataTransfer?.files)
}
</script>

<template>
  <div>
    <div
      :class="
        cn(
          'flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border-strong bg-surface-sunken text-center transition-colors',
          compact ? 'px-3 py-3' : 'px-4 py-8',
          dragging && 'border-brand bg-surface-selected',
          disabled && 'opacity-50',
        )
      "
      data-testid="file-drop"
      @dragover.prevent="dragging = !disabled"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
    >
      <Upload v-if="!compact" class="size-5 text-ink-muted" aria-hidden="true" />
      <button
        type="button"
        class="text-body-strong text-brand-ink hover:underline disabled:pointer-events-none"
        :disabled="disabled || busy"
        @click="input?.click()"
      >
        {{ busy ? `Uploading… ${Math.round((progress ?? 0) * 100)}%` : label }}
      </button>
      <p v-if="hint" class="text-caption text-ink-muted">{{ hint }}</p>
      <input
        ref="input"
        type="file"
        multiple
        class="sr-only"
        tabindex="-1"
        aria-hidden="true"
        :accept="accept"
        :disabled="disabled || busy"
        @change="take(($event.target as HTMLInputElement).files)"
      />
    </div>
    <p v-if="error" class="mt-1 text-caption text-danger" role="alert">{{ error }}</p>
  </div>
</template>
