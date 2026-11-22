<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { ChatMessage } from '../store'
import AnswerMessage from './AnswerMessage.vue'

// The thread: each turn is the question (plain text, never HTML) and its answer.
const props = defineProps<{ messages: ChatMessage[]; active: { messageId: string; n: number } | null }>()
const emit = defineEmits<{ cite: [messageId: string, n: number]; retry: [messageId: string] }>()

const end = ref<HTMLElement | null>(null)

// Follow the answer as it grows.
watch(
  () => props.messages.map((m) => m.answer.length).join(','),
  async () => {
    await nextTick()
    end.value?.scrollIntoView?.({ block: 'end' })
  },
)
</script>

<template>
  <ol class="flex flex-col gap-8" aria-label="Conversation" data-testid="message-list">
    <li v-for="m in messages" :key="m.id" class="flex flex-col gap-3">
      <p
        class="max-w-[85%] self-end rounded-lg bg-surface-selected px-3 py-2 text-body whitespace-pre-wrap text-ink"
        data-testid="question"
      >
        {{ m.question }}
      </p>
      <AnswerMessage
        :message="m"
        :active-n="active?.messageId === m.id ? active.n : null"
        @cite="emit('cite', m.id, $event)"
        @retry="emit('retry', m.id)"
      />
    </li>
    <li ref="end" aria-hidden="true" />
  </ol>
</template>
