<script setup lang="ts">
import { computed, ref } from 'vue'
import { LogOut, Menu, Monitor, Moon, Sun, X } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { applyTheme, isThemeChoice, readStoredTheme, type ThemeChoice } from '@/lib/theme'
import { useUserStore } from '@/stores/user'

/**
 * The top bar over the content column (SPEC-07 §3, §8): the demo user switcher (or, in password
 * mode, the signed-in user and Sign out) and the theme toggle on the right. Phones: the menu button
 * and org name on the left.
 */
const drawerOpen = defineModel<boolean>('drawerOpen', { default: false })
const user = useUserStore()

const selected = computed({
  get: () => user.userId ?? '',
  set: (id: string) => user.setUser(id || null),
})

const theme = ref<ThemeChoice>(readStoredTheme())
function onTheme(value: unknown) {
  if (!isThemeChoice(value)) return
  theme.value = value
  applyTheme(value)
}
const themeIcon = computed(() => (theme.value === 'dark' ? Moon : theme.value === 'light' ? Sun : Monitor))
</script>

<template>
  <header
    class="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-2 border-b bg-surface px-4 md:px-6"
    data-testid="top-bar"
  >
    <div class="flex min-w-0 flex-1 items-center gap-2 md:hidden">
      <button
        type="button"
        class="rounded-md p-1.5 hover:bg-surface-hover"
        :aria-label="drawerOpen ? 'Close navigation' : 'Open navigation'"
        :aria-expanded="drawerOpen"
        @click="drawerOpen = !drawerOpen"
      >
        <X v-if="drawerOpen" class="size-5" /><Menu v-else class="size-5" />
      </button>
      <span class="min-w-0 flex-1 truncate text-body-strong">{{ user.orgName }}</span>
    </div>
    <div class="max-md:hidden md:flex-1" />

    <Skeleton v-if="user.loading && !user.config" class="h-(--control-h) w-44" />
    <p v-else-if="user.error" class="text-caption text-danger" role="alert">
      {{
        user.isPassword ? user.error : "Can't load demo users. Check that the API is running, then reload."
      }}
    </p>
    <span
      v-else-if="user.isPassword && user.me"
      class="min-w-0 truncate text-caption text-ink-muted max-md:hidden"
      data-testid="signed-in-user"
      >{{ user.me.name }}</span
    >
    <Select
      v-else-if="user.demoUsers.length"
      v-model="selected"
      class="w-44"
      aria-label="Demo user"
      data-testid="demo-user-select"
    >
      <option v-for="u in user.demoUsers" :key="u.id" :value="u.id">{{ u.name }}</option>
    </Select>

    <Button v-if="user.isPassword" variant="ghost" size="sm" data-testid="sign-out" @click="user.logout()">
      <LogOut aria-hidden="true" /> Sign out
    </Button>

    <DropdownMenu>
      <DropdownMenuTrigger as-child>
        <Button variant="ghost" size="icon" aria-label="Theme" title="Theme">
          <component :is="themeIcon" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Theme</DropdownMenuLabel>
        <DropdownMenuRadioGroup :model-value="theme" @update:model-value="onTheme">
          <DropdownMenuRadioItem value="light">Light</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="dark">Dark</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="system">System</DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  </header>
</template>
