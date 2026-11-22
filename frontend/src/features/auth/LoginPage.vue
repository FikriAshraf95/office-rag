<script setup lang="ts">
import { ref } from 'vue'
import { toProblem } from '@/api/http'
import { Banner } from '@/components/ui/banner'
import { Button } from '@/components/ui/button'
import { Input, PasswordInput } from '@/components/ui/input'
import { useUserStore } from '@/stores/user'

/**
 * The sign-in page for password mode (SPEC-07 §8, SPEC-11 §5.2). Shown instead of the app shell while
 * there is no session. The session itself is an HttpOnly cookie; this page never stores the password.
 */
const user = useUserStore()
const username = ref('')
const password = ref('')
const busy = ref(false)
const error = ref<string | null>(null)

async function submit() {
  if (!username.value.trim() || !password.value) {
    error.value = 'Enter your username and password.'
    return
  }
  busy.value = true
  error.value = null
  try {
    await user.login(username.value, password.value)
  } catch (e) {
    const problem = toProblem(e)
    error.value =
      problem.code === 'bad_credentials' ? 'The username or password is wrong. Try again.' : problem.detail
    password.value = ''
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="flex min-h-full items-center justify-center bg-surface-sunken p-4">
    <form
      class="flex w-full max-w-sm flex-col gap-4 rounded-lg border bg-surface p-6 shadow-sm"
      data-testid="login-form"
      novalidate
      @submit.prevent="submit"
    >
      <div class="flex flex-col gap-1">
        <h1 class="text-title-lg text-ink">{{ user.orgName }}</h1>
        <p class="text-body text-ink-muted">Sign in to ask about company documents.</p>
      </div>

      <Banner v-if="error" tone="danger" role="alert">{{ error }}</Banner>

      <label class="flex flex-col gap-1 text-caption text-ink-muted">
        Username
        <Input
          v-model="username"
          name="username"
          autocomplete="username"
          autocapitalize="none"
          spellcheck="false"
          :aria-invalid="!!error"
          autofocus
        />
      </label>
      <label class="flex flex-col gap-1 text-caption text-ink-muted">
        Password
        <PasswordInput
          v-model="password"
          name="password"
          autocomplete="current-password"
          :aria-invalid="!!error"
        />
      </label>

      <Button type="submit" variant="primary" :disabled="busy">{{ busy ? 'Signing in…' : 'Sign in' }}</Button>
    </form>
  </main>
</template>
