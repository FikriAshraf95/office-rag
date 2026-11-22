<script setup lang="ts">
import { ChartColumn } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { toProblem } from '@/api/http'
import EmptyState from '@/components/common/EmptyState.vue'
import PageContainer from '@/components/common/PageContainer.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { Banner } from '@/components/ui/banner'
import { Skeleton } from '@/components/ui/skeleton'
import { DataTable } from '@/components/ui/table'
import { formatDateTime } from '@/lib/format'
import { usageApi, type UsageSummary } from './api'

// SPEC-07 §7: questions and ingestion stat rows, a table by model × purpose, latest balances.
const summary = ref<UsageSummary | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    summary.value = await usageApi.summary()
  } catch (e) {
    error.value = toProblem(e).detail
  } finally {
    loading.value = false
  }
})

const number = new Intl.NumberFormat('en-MY')
const n = (value: number | null | undefined) => (value == null ? '–' : number.format(Math.round(value)))
const seconds = (ms: number | null | undefined) => (ms == null ? '–' : `${(ms / 1000).toFixed(1)} s`)
const myr = (value: number | null | undefined) => (value == null ? 'Plan quota' : `RM ${value.toFixed(2)}`)

const empty = computed(
  () => !!summary.value && !summary.value.byModel.length && !summary.value.questions.count,
)

const questionStats = computed(() => {
  const q = summary.value?.questions
  return [
    { label: 'Questions', value: n(q?.count) },
    { label: 'Average latency', value: seconds(q?.avgLatencyMs) },
    { label: 'Average tokens', value: n(q?.avgTokens) },
  ]
})
const ingestionStats = computed(() => {
  const i = summary.value?.ingestion
  return [
    { label: 'Documents', value: n(i?.documents) },
    { label: 'Chunks', value: n(i?.chunks) },
    { label: 'Embedding tokens', value: n(i?.embedTokens) },
  ]
})
</script>

<template>
  <PageContainer width="wide">
    <PageHeader title="Usage" description="Tokens and cost by model and purpose." />

    <div v-if="loading" class="flex flex-col gap-3" role="status">
      <span class="sr-only">Loading usage…</span>
      <Skeleton class="h-20 w-full" />
      <Skeleton class="h-20 w-full" />
      <Skeleton class="h-40 w-full" />
    </div>
    <Banner v-else-if="error" tone="danger">{{ error }}</Banner>
    <Banner v-if="summary?.balances.paygLow" tone="warning" data-testid="payg-low">
      The PAYG balance is low. Top it up before the AI service starts refusing questions.
    </Banner>
    <EmptyState
      v-else-if="empty"
      :icon="ChartColumn"
      title="No usage yet"
      description="Ask a question or upload a document, and the totals appear here."
    />
    <template v-else-if="summary">
      <section
        v-for="row in [
          { title: 'Questions', stats: questionStats },
          { title: 'Ingestion', stats: ingestionStats },
        ]"
        :key="row.title"
        :aria-label="row.title"
        class="grid gap-3 sm:grid-cols-3"
      >
        <div v-for="s in row.stats" :key="s.label" class="rounded-lg border bg-surface px-4 py-3 shadow-sm">
          <p class="text-caption text-ink-muted">{{ row.title }} · {{ s.label }}</p>
          <p class="mt-1 text-title-lg text-ink">{{ s.value }}</p>
        </div>
      </section>

      <section class="flex flex-col gap-2" aria-label="By model and purpose">
        <h2 class="text-title text-ink">By model and purpose</h2>
        <DataTable aria-label="Usage by model and purpose" data-testid="usage-table">
          <thead>
            <tr>
              <th scope="col">Model</th>
              <th scope="col">Purpose</th>
              <th scope="col" class="text-right">Calls</th>
              <th scope="col" class="text-right">Prompt tokens</th>
              <th scope="col" class="text-right">Completion tokens</th>
              <th scope="col" class="text-right">Cost</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in summary.byModel" :key="`${row.model}-${row.role}-${row.purpose}`">
              <td class="text-ink">{{ row.model }}</td>
              <td class="text-ink-muted">{{ row.purpose }}</td>
              <td class="text-right">{{ n(row.calls) }}</td>
              <td class="text-right">{{ n(row.promptTokens) }}</td>
              <td class="text-right">{{ n(row.completionTokens) }}</td>
              <td class="text-right">{{ myr(row.costMyr) }}</td>
            </tr>
          </tbody>
        </DataTable>
      </section>

      <section class="flex flex-col gap-2" aria-label="Latest balances">
        <h2 class="text-title text-ink">Latest balances</h2>
        <dl class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-lg border bg-surface px-4 py-3 shadow-sm">
            <dt class="text-caption text-ink-muted">Plan tokens left</dt>
            <dd class="mt-1 text-title-lg text-ink">{{ n(summary.balances.planTokens) }}</dd>
          </div>
          <div class="rounded-lg border bg-surface px-4 py-3 shadow-sm">
            <dt class="text-caption text-ink-muted">Pay-as-you-go left</dt>
            <dd class="mt-1 text-title-lg text-ink">
              {{ summary.balances.paygMyr == null ? '–' : `RM ${summary.balances.paygMyr.toFixed(2)}` }}
            </dd>
          </div>
        </dl>
        <p class="text-caption text-ink-muted">
          {{
            summary.balances.readAt
              ? `Read from the provider on ${formatDateTime(summary.balances.readAt)}.`
              : 'No balance read from the provider yet.'
          }}
        </p>
      </section>
    </template>
  </PageContainer>
</template>
