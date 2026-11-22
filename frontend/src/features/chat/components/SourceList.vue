<script setup lang="ts">
import { ChevronDown, ChevronRight, File, FileSpreadsheet, FileText, Image } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { formatDate } from '@/lib/format'
import type { Source } from '../api'

// Cited sources as cards, then a collapsed "Other sources searched (k)" list (SPEC-07 §5.3).
const props = defineProps<{ sources: Source[]; cited: number[]; activeN?: number | null }>()
const emit = defineEmits<{ open: [n: number] }>()

const primary = computed(() => props.sources.filter((s) => props.cited.includes(s.n)))
const others = computed(() => props.sources.filter((s) => !props.cited.includes(s.n)))
const showOthers = ref(false)

function iconFor(fileType: string) {
  if (fileType === 'xlsx') return FileSpreadsheet
  if (fileType === 'png' || fileType === 'jpg' || fileType === 'jpeg') return Image
  if (fileType === 'pdf' || fileType === 'docx' || fileType === 'md') return FileText
  return File
}

function where(s: Source): string {
  if (s.sheet) return `Sheet ${s.sheet}`
  if (s.pageStart == null) return s.section ? `Section ${s.section}` : ''
  return s.pageEnd && s.pageEnd !== s.pageStart ? `Pages ${s.pageStart}–${s.pageEnd}` : `Page ${s.pageStart}`
}

function path(s: Source): string {
  return s.headingPath.slice(1).join(' › ')
}
</script>

<template>
  <section v-if="sources.length" class="flex flex-col gap-2" aria-label="Sources">
    <h3 v-if="primary.length" class="text-caption font-medium text-ink-muted">Sources</h3>
    <ul v-if="primary.length" class="flex flex-col gap-2" data-testid="source-cards">
      <li v-for="s in primary" :key="s.n">
        <button
          type="button"
          :class="[
            'flex w-full items-start gap-3 rounded-lg border bg-surface px-3 py-2.5 text-left shadow-sm hover:bg-surface-hover',
            activeN === s.n && 'bg-surface-selected',
          ]"
          :aria-label="`Open source ${s.n}: ${s.title}`"
          @click="emit('open', s.n)"
        >
          <span
            class="flex size-6 shrink-0 items-center justify-center rounded-sm bg-surface-selected text-caption font-semibold text-brand-ink"
            aria-hidden="true"
            >{{ s.n }}</span
          >
          <component
            :is="iconFor(s.fileType)"
            class="mt-0.5 size-4 shrink-0 text-ink-muted"
            aria-hidden="true"
          />
          <span class="min-w-0 flex-1">
            <span class="block truncate text-body-strong text-ink">{{ s.title }}</span>
            <span v-if="path(s)" class="block truncate text-caption text-ink-muted">{{ path(s) }}</span>
            <span class="block text-caption text-ink-muted">
              {{
                [where(s), s.effectiveDate ? `Effective ${formatDate(s.effectiveDate)}` : '']
                  .filter(Boolean)
                  .join(' · ')
              }}
            </span>
          </span>
        </button>
      </li>
    </ul>

    <div v-if="others.length">
      <button
        type="button"
        class="flex items-center gap-1 rounded-sm text-caption text-ink-muted hover:text-ink"
        :aria-expanded="showOthers"
        @click="showOthers = !showOthers"
      >
        <component :is="showOthers ? ChevronDown : ChevronRight" class="size-4" aria-hidden="true" />
        Other sources searched ({{ others.length }})
      </button>
      <ul
        v-if="showOthers"
        class="mt-2 flex flex-col divide-y rounded-lg border bg-surface"
        data-testid="other-sources"
      >
        <li v-for="s in others" :key="s.n">
          <button
            type="button"
            class="flex w-full items-center gap-2 px-3 py-2 text-left text-cell hover:bg-surface-hover"
            @click="emit('open', s.n)"
          >
            <component :is="iconFor(s.fileType)" class="size-4 shrink-0 text-ink-muted" aria-hidden="true" />
            <span class="min-w-0 flex-1 truncate text-ink">{{ s.title }}</span>
            <span class="shrink-0 text-caption text-ink-muted">{{ where(s) }}</span>
          </button>
        </li>
      </ul>
    </div>
  </section>
</template>
