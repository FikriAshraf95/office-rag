<script setup lang="ts">
import {
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogOverlay,
  AlertDialogPortal,
  AlertDialogRoot,
  AlertDialogTitle,
} from 'reka-ui'
import { buttonVariants } from '@/components/ui/button'

// A confirmation that names its action ("Sign out", not "OK"). Danger buttons live only here.
withDefaults(
  defineProps<{
    title: string
    description?: string
    confirmLabel: string
    cancelLabel?: string
    danger?: boolean
  }>(),
  { cancelLabel: 'Cancel', danger: false },
)
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ confirm: [] }>()

// Not AlertDialogAction: it closes the dialog from its own click handler, which can run before ours.
// A page that clears its target when the dialog closes would then confirm nothing. Confirm first, then close.
function confirm() {
  emit('confirm')
  open.value = false
}
</script>

<template>
  <AlertDialogRoot v-model:open="open">
    <AlertDialogPortal>
      <AlertDialogOverlay
        class="fixed inset-0 z-50 bg-scrim data-[state=open]:animate-in data-[state=open]:fade-in-0"
      />
      <AlertDialogContent
        class="fixed top-1/2 left-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-surface p-4 shadow-lg"
      >
        <AlertDialogTitle class="text-title text-ink">{{ title }}</AlertDialogTitle>
        <AlertDialogDescription v-if="description" class="mt-2 text-body text-ink-muted">
          {{ description }}
        </AlertDialogDescription>
        <div class="mt-6 flex justify-end gap-2">
          <AlertDialogCancel :class="buttonVariants({ variant: 'secondary' })">{{
            cancelLabel
          }}</AlertDialogCancel>
          <button
            type="button"
            :class="buttonVariants({ variant: danger ? 'danger' : 'primary' })"
            @click="confirm"
          >
            {{ confirmLabel }}
          </button>
        </div>
      </AlertDialogContent>
    </AlertDialogPortal>
  </AlertDialogRoot>
</template>
