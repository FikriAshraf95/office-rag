<script setup lang="ts">
import { FileImage, FileSpreadsheet, FileText, MoreHorizontal } from 'lucide-vue-next'
import type { Component } from 'vue'
import { RouterLink } from 'vue-router'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { StatusPill } from '@/components/ui/status-pill'
import { DataTable } from '@/components/ui/table'
import { formatDate } from '@/lib/format'
import type { Document } from '../api'
import { isActive } from '../store'
import IngestStatusPill from './IngestStatusPill.vue'

// SPEC-07 §6.2: a table from tablet width up, a card list on phones. Row actions appear on hover or focus.
defineProps<{ documents: Document[] }>()
const emit = defineEmits<{
  open: [doc: Document]
  edit: [doc: Document]
  reingest: [doc: Document]
  toggleStatus: [doc: Document]
  remove: [doc: Document]
}>()

const icons: Record<string, Component> = {
  pdf: FileText,
  docx: FileText,
  md: FileText,
  xlsx: FileSpreadsheet,
  png: FileImage,
  jpg: FileImage,
}
const iconFor = (doc: Document) => icons[doc.fileType] ?? FileText

const MAX_CHIPS = 2
const shown = (doc: Document) => doc.accessGroups.slice(0, MAX_CHIPS)
const hidden = (doc: Document) => Math.max(0, doc.accessGroups.length - MAX_CHIPS)
const statusLabel = (doc: Document) => (doc.status === 'current' ? 'Current' : 'Superseded')
const statusColor = (doc: Document) => (doc.status === 'current' ? 'green' : 'grey')
const toggleLabel = (doc: Document) => (doc.status === 'current' ? 'Mark superseded' : 'Mark current')
</script>

<template>
  <div>
    <DataTable class="hidden md:block" aria-label="Documents" data-testid="documents-table">
      <thead>
        <tr>
          <th scope="col">Title</th>
          <th scope="col">Type</th>
          <th scope="col">Department</th>
          <th scope="col">Effective</th>
          <th scope="col">Status</th>
          <th scope="col">Ingestion</th>
          <th scope="col" class="text-right">Chunks</th>
          <th scope="col">Access</th>
          <th scope="col">Uploaded</th>
          <th scope="col"><span class="sr-only">Actions</span></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="doc in documents" :key="doc.id" class="group" data-testid="document-row">
          <td class="max-w-72">
            <RouterLink
              :to="{ name: 'document', params: { id: doc.id } }"
              class="flex items-center gap-2 text-body-strong text-ink hover:text-brand-ink"
            >
              <component :is="iconFor(doc)" class="size-4 shrink-0 text-ink-muted" aria-hidden="true" />
              <span class="truncate" :title="doc.summary ?? doc.title">{{ doc.title }}</span>
            </RouterLink>
          </td>
          <td class="text-ink-muted">{{ doc.docType }}</td>
          <td class="text-ink-muted">{{ doc.department ?? '–' }}</td>
          <td class="whitespace-nowrap text-ink-muted">
            {{ doc.effectiveDate ? formatDate(doc.effectiveDate) : '–' }}
          </td>
          <td><StatusPill :color="statusColor(doc)" :label="statusLabel(doc)" /></td>
          <td><IngestStatusPill :status="doc.ingestStatus" :error="doc.ingestError" /></td>
          <td class="text-right text-ink-muted tabular-nums">{{ doc.chunkCount }}</td>
          <td>
            <span class="flex gap-1">
              <Badge v-for="g in shown(doc)" :key="g">{{ g }}</Badge>
              <Badge v-if="hidden(doc)" :title="doc.accessGroups.join(', ')">+{{ hidden(doc) }}</Badge>
            </span>
          </td>
          <td class="whitespace-nowrap text-ink-muted">{{ formatDate(doc.createdAt) }}</td>
          <td class="text-right">
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button
                  variant="ghost"
                  size="icon"
                  :aria-label="`Actions for ${doc.title}`"
                  class="md:opacity-0 md:group-focus-within:opacity-100 md:group-hover:opacity-100 data-[state=open]:opacity-100"
                >
                  <MoreHorizontal />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem @select="emit('open', doc)">Open</DropdownMenuItem>
                <DropdownMenuItem @select="emit('edit', doc)">Edit details</DropdownMenuItem>
                <DropdownMenuItem :disabled="isActive(doc)" @select="emit('reingest', doc)"
                  >Re-ingest</DropdownMenuItem
                >
                <DropdownMenuItem @select="emit('toggleStatus', doc)">{{
                  toggleLabel(doc)
                }}</DropdownMenuItem>
                <DropdownMenuItem class="text-danger" @select="emit('remove', doc)">Delete</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </td>
        </tr>
      </tbody>
    </DataTable>

    <ul class="flex flex-col gap-3 md:hidden" aria-label="Documents">
      <li v-for="doc in documents" :key="doc.id" class="rounded-lg border bg-surface p-3 shadow-sm">
        <div class="flex items-start justify-between gap-2">
          <RouterLink
            :to="{ name: 'document', params: { id: doc.id } }"
            class="flex min-w-0 items-center gap-2 text-body-strong text-ink"
          >
            <component :is="iconFor(doc)" class="size-4 shrink-0 text-ink-muted" aria-hidden="true" />
            <span class="truncate">{{ doc.title }}</span>
          </RouterLink>
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button variant="ghost" size="icon" :aria-label="`Actions for ${doc.title}`"
                ><MoreHorizontal
              /></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem @select="emit('open', doc)">Open</DropdownMenuItem>
              <DropdownMenuItem @select="emit('edit', doc)">Edit details</DropdownMenuItem>
              <DropdownMenuItem :disabled="isActive(doc)" @select="emit('reingest', doc)"
                >Re-ingest</DropdownMenuItem
              >
              <DropdownMenuItem @select="emit('toggleStatus', doc)">{{ toggleLabel(doc) }}</DropdownMenuItem>
              <DropdownMenuItem class="text-danger" @select="emit('remove', doc)">Delete</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <div class="mt-2 flex flex-wrap items-center gap-2">
          <StatusPill :color="statusColor(doc)" :label="statusLabel(doc)" />
          <IngestStatusPill :status="doc.ingestStatus" :error="doc.ingestError" />
        </div>
        <p class="mt-2 text-caption text-ink-muted">
          {{ doc.docType }} · {{ doc.department ?? 'No department' }} · {{ doc.chunkCount }} chunks ·
          {{ formatDate(doc.createdAt) }}
        </p>
      </li>
    </ul>
  </div>
</template>
