<script setup lang="ts">
import { AlertTriangle, CheckCircle2, Info, OctagonAlert } from 'lucide-vue-next'
import { computed, type HTMLAttributes } from 'vue'

// A plain class list, not cn(): twMerge would drop text-body next to the tone colour.
// A full-width message on a *-soft token (design-system §10). Danger announces itself (role=alert);
// the others are role=status only when the caller asks, because most are static notes. `action` holds
// a button or link; `class` adds spacing.
const props = withDefaults(
  defineProps<{ tone?: 'info' | 'warning' | 'success' | 'danger'; class?: HTMLAttributes['class'] }>(),
  { tone: 'info' },
)
const tones = {
  info: { icon: Info, box: 'bg-info-soft text-info' },
  warning: { icon: AlertTriangle, box: 'bg-warning-soft text-warning' },
  success: { icon: CheckCircle2, box: 'bg-success-soft text-success' },
  danger: { icon: OctagonAlert, box: 'bg-danger-soft text-danger' },
}
const tone = computed(() => tones[props.tone])
</script>

<template>
  <div
    :role="props.tone === 'danger' ? 'alert' : undefined"
    :class="['flex items-start gap-2.5 rounded-lg px-3 py-2.5 text-body', tone.box, props.class]"
  >
    <component :is="tone.icon" class="mt-0.5 size-4 shrink-0" aria-hidden="true" />
    <div class="min-w-0 flex-1"><slot /></div>
    <div v-if="$slots.action" class="flex shrink-0 items-center gap-2"><slot name="action" /></div>
  </div>
</template>
