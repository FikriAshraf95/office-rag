<script setup lang="ts">
import type { HTMLAttributes } from 'vue'

// The shared list table (design-system §10), modelled on the Admin Users table: a rounded card with a
// soft shadow that scrolls sideways, a sunken header row, comfortable rows and a hover fill. It is still
// a real `<table>`: write `<thead>`, `<tbody>`, `<tr>`, `<th>` and `<td>` as children, so the look
// lives here once. `class` goes on the card; data-testid, aria-label and every other attribute go to
// the `<table>`. Not for the board grid, Gantt, calendar or doc tables.
defineOptions({ inheritAttrs: false })
defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div
    :class="[
      'overflow-x-auto rounded-lg border bg-surface shadow-sm',
      '[&_thead]:border-b [&_thead]:bg-surface-sunken [&_thead]:text-caption [&_thead]:text-ink-muted',
      '[&_th]:px-3 [&_th]:py-2.5 [&_th]:font-medium',
      '[&_td]:px-3 [&_td]:py-3',
      '[&_tbody]:divide-y [&_tbody_tr:hover]:bg-surface-hover',
      $props.class,
    ]"
  >
    <table v-bind="$attrs" class="w-full text-left text-body">
      <slot />
    </table>
  </div>
</template>
