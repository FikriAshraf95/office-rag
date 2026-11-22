<script setup lang="ts">
// The one page-width wrapper (SPEC-21 §5.1): left-aligned under the main gutter like board pages.
// `wide` fills the window; `reading` is capped at --page-w-reading for forms. Never centred.
withDefaults(defineProps<{ width?: 'wide' | 'reading' }>(), { width: 'wide' })
</script>

<template>
  <div class="flex w-full flex-col gap-6" :class="width === 'reading' && 'max-w-(--page-w-reading)'">
    <slot />
  </div>
</template>
