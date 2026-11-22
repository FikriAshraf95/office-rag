<script setup lang="ts">
import { Maximize, ZoomIn, ZoomOut } from 'lucide-vue-next'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Button } from '@/components/ui/button'

// PNG/JPG sources (SPEC-07 §5.4), adapted from Private Repo App's ImageLightbox: the same zoom, but
// inline in the panel and fed a Blob (fetched with X-Demo-User), so no direct URL to the API. The
// object URL is revoked when the image changes or the panel closes.
const props = defineProps<{ blob: Blob; alt: string }>()

const MIN = 0.5
const MAX = 4
const STEP = 1.25

const scale = ref(1)
const url = ref('')

watch(
  () => props.blob,
  (blob) => {
    if (url.value) URL.revokeObjectURL(url.value)
    url.value = URL.createObjectURL(blob)
    scale.value = 1
  },
  { immediate: true },
)
onBeforeUnmount(() => {
  if (url.value) URL.revokeObjectURL(url.value)
})

const clamp = (value: number) => Math.min(MAX, Math.max(MIN, value))
const zoomIn = () => (scale.value = clamp(scale.value * STEP))
const zoomOut = () => (scale.value = clamp(scale.value / STEP))
const reset = () => (scale.value = 1)
const width = computed(() => `${scale.value * 100}%`)
</script>

<template>
  <div class="flex flex-col gap-2" data-testid="image-viewer">
    <div class="flex items-center gap-1">
      <Button variant="ghost" size="icon" aria-label="Zoom out" :disabled="scale <= MIN" @click="zoomOut">
        <ZoomOut />
      </Button>
      <span class="w-12 text-center text-caption text-ink-muted" aria-live="polite"
        >{{ Math.round(scale * 100) }}%</span
      >
      <Button variant="ghost" size="icon" aria-label="Zoom in" :disabled="scale >= MAX" @click="zoomIn">
        <ZoomIn />
      </Button>
      <Button variant="ghost" size="icon" aria-label="Fit to panel" @click="reset"><Maximize /></Button>
    </div>
    <div class="max-h-[60vh] overflow-auto rounded-lg border bg-surface-sunken p-2">
      <img :src="url" :alt="alt" :style="{ width }" class="max-w-none" draggable="false" />
    </div>
  </div>
</template>
