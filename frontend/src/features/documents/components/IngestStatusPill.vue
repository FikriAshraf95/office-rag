<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next'
import { computed } from 'vue'
import { StatusPill } from '@/components/ui/status-pill'
import { Tooltip } from '@/components/ui/tooltip'
import type { Document } from '../api'

// SPEC-07 §6.2: queued → grey, processing → blue with a spinner, ready → green, failed → red with the error in a tooltip.
const props = defineProps<{ status: Document['ingestStatus']; error?: string | null }>()

const looks = {
  queued: { color: 'grey', label: 'Queued' },
  processing: { color: 'blue', label: 'Processing' },
  ready: { color: 'green', label: 'Ready' },
  failed: { color: 'red', label: 'Failed' },
} as const
const look = computed(() => looks[props.status])
</script>

<template>
  <Tooltip :text="status === 'failed' ? (error ?? undefined) : undefined">
    <span class="inline-flex items-center gap-1.5" data-testid="ingest-pill" :data-status="status">
      <StatusPill :color="look.color" :label="look.label" />
      <Loader2
        v-if="status === 'processing'"
        class="size-3.5 animate-spin text-label-blue"
        aria-hidden="true"
        data-testid="ingest-spinner"
      />
    </span>
  </Tooltip>
</template>
