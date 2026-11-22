<script setup lang="ts">
import { MessageSquare, Plus } from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PageContainer from '@/components/common/PageContainer.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { Button } from '@/components/ui/button'
import SourcePanel from '@/features/viewer/SourcePanel.vue'
import Composer from './components/Composer.vue'
import MessageList from './components/MessageList.vue'
import { useChatStore } from './store'

// SPEC-07 §5: the thread in a reading-width column, the SourcePanel beside it (≥ 1280px) or over it.
const chat = useChatStore()
const composer = ref<InstanceType<typeof Composer> | null>(null)
const active = ref<{ messageId: string; n: number } | null>(null)

const EXAMPLES = [
  'How do I apply for annual leave?',
  'How many days of annual leave does a grade M2 employee get?',
  'What is the deadline to submit a claim?',
  'Bilakah syarikat ditutup pada hujung tahun?',
]

const activeSource = computed(() => {
  if (!active.value) return null
  const message = chat.messages.find((m) => m.id === active.value?.messageId)
  return message?.sources.find((s) => s.n === active.value?.n) ?? null
})

function openSource(messageId: string, n: number) {
  active.value = { messageId, n }
}

function send(question: string) {
  active.value = null
  void chat.send(question)
}

function newChat() {
  chat.clear()
  active.value = null
}

// A cleared thread (New chat, or a different demo user) closes the panel.
watch(
  () => chat.messages.length,
  (length) => {
    if (!length) active.value = null
  },
)

// `/` focuses the composer; Esc closes the SourcePanel (SPEC-07 §9).
function onKey(event: KeyboardEvent) {
  const target = event.target as HTMLElement | null
  const typing = !!target && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))
  if (event.key === 'Escape' && active.value) {
    active.value = null
  } else if (event.key === '/' && !typing && !event.metaKey && !event.ctrlKey) {
    event.preventDefault()
    composer.value?.focus()
  }
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="flex items-start gap-6">
    <PageContainer width="reading" class="min-w-0 flex-1">
      <PageHeader title="Chat" description="Ask questions and get cited answers from company documents.">
        <template v-if="chat.messages.length" #actions>
          <Button :disabled="chat.streaming" @click="newChat"><Plus /> New chat</Button>
        </template>
      </PageHeader>

      <EmptyState
        v-if="!chat.messages.length"
        :icon="MessageSquare"
        title="Ask about company documents"
        description="Answers come only from the documents you can access, and every claim is cited."
      >
        <ul class="flex max-w-md flex-col gap-2" aria-label="Example questions">
          <li v-for="q in EXAMPLES" :key="q">
            <Button class="h-auto w-full justify-start py-2 text-left whitespace-normal" @click="send(q)">
              {{ q }}
            </Button>
          </li>
        </ul>
      </EmptyState>

      <MessageList
        v-else
        :messages="chat.messages"
        :active="active"
        @cite="openSource"
        @retry="chat.retry($event)"
      />

      <div class="sticky bottom-0 -mx-1 bg-surface-page px-1 pt-2 pb-1">
        <Composer ref="composer" :streaming="chat.streaming" @send="send" @stop="chat.stop()" />
      </div>
    </PageContainer>

    <SourcePanel v-if="activeSource" :source="activeSource" @close="active = null" />
  </div>
</template>
