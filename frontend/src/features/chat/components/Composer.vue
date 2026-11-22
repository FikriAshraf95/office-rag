<script setup lang="ts">
import { ArrowUp, Square } from 'lucide-vue-next'
import { computed, nextTick, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/input'
import { MAX_QUESTION_LENGTH } from '../store'

// SPEC-07 §5.2: grows to 6 lines; Enter sends, Shift+Enter adds a line; counter after 800
// characters; while streaming the one primary button becomes Stop.
const props = defineProps<{ streaming: boolean }>()
const emit = defineEmits<{ send: [question: string]; stop: [] }>()

const text = ref('')
const field = ref<{ $el: HTMLTextAreaElement } | null>(null)
const COUNTER_FROM = 800
const LINE_PX = 20
const MAX_LINES = 6

const length = computed(() => text.value.length)
const tooLong = computed(() => length.value > MAX_QUESTION_LENGTH)
const canSend = computed(() => text.value.trim() !== '' && !tooLong.value)

function textarea(): HTMLTextAreaElement | null {
  return field.value?.$el ?? null
}

function grow() {
  const el = textarea()
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, LINE_PX * MAX_LINES + 16)}px`
}

function submit() {
  if (props.streaming || !canSend.value) return
  emit('send', text.value.trim())
  text.value = ''
  void nextTick(grow)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    submit()
  }
}

defineExpose({ focus: () => textarea()?.focus() })
</script>

<template>
  <form class="flex flex-col gap-1" @submit.prevent="submit">
    <div class="flex items-end gap-2">
      <Textarea
        ref="field"
        v-model="text"
        rows="1"
        class="min-h-(--control-h) flex-1 resize-none"
        placeholder="Ask about company documents"
        aria-label="Your question"
        :aria-invalid="tooLong"
        @input="grow"
        @keydown="onKeydown"
      />
      <Button v-if="streaming" type="button" variant="primary" aria-label="Stop" @click="emit('stop')">
        <Square /> Stop
      </Button>
      <Button v-else type="submit" variant="primary" :disabled="!canSend" aria-label="Send">
        <ArrowUp /> Send
      </Button>
    </div>
    <p
      v-if="length >= COUNTER_FROM"
      :class="['text-caption', tooLong ? 'text-danger' : 'text-ink-muted']"
      aria-live="polite"
    >
      {{ length }} / {{ MAX_QUESTION_LENGTH
      }}<template v-if="tooLong"> – shorten the question to send it.</template>
    </p>
  </form>
</template>
