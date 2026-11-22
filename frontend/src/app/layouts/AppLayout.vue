<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { PanelLeftClose, PanelLeftOpen } from 'lucide-vue-next'
import { initials } from '@/lib/colors'
import { cn } from '@/lib/utils'
import { navigation, type NavItem } from '@/app/navigation'
import { useUserStore } from '@/stores/user'
import AppTopBar from './AppTopBar.vue'
import { useSidebarStore } from './sidebar'

// The app shell (SPEC-07 §3), copied from Office Suite without realtime, notifications, search or
// the workspace tree. The sidebar holds Chat, Documents and Usage.
const user = useUserStore()
const route = useRoute()
const sidebar = useSidebarStore()
// The rail only exists from 768px up; the mobile drawer is always full width.
const rail = computed(() => sidebar.rail)
const hiddenInRail = computed(() => (rail.value ? 'md:hidden' : ''))
const mobileOpen = ref(false)
watch(
  () => route.fullPath,
  () => (mobileOpen.value = false),
)

// `/config` gives the demo users and the org name; it runs before a user is chosen (SPEC-07 §8).
onMounted(() => {
  if (!user.config) void user.load()
})

// The current entry: selected surface, medium weight and a 2px brand bar on the left.
const navClass = computed(() =>
  cn(
    'relative flex items-center gap-3 rounded-md px-3 py-1.5 text-body text-ink hover:bg-surface-hover',
    rail.value && 'md:justify-center md:px-0',
  ),
)
const navActive =
  'bg-surface-selected font-medium text-brand-ink hover:bg-surface-selected before:absolute before:inset-y-1.5 before:left-0 before:w-0.5 before:rounded-full before:bg-brand'
const isCurrent = (item: NavItem) =>
  route.name === item.routeName || (item.alsoActiveFor ?? []).includes(String(route.name))
</script>

<template>
  <div class="flex h-full">
    <div v-if="mobileOpen" class="fixed inset-0 z-30 bg-scrim md:hidden" @click="mobileOpen = false" />

    <aside
      :class="[
        'fixed inset-y-0 left-0 z-40 flex w-(--sidebar-w) flex-col border-r bg-surface transition-transform md:static md:translate-x-0',
        rail ? 'md:w-(--sidebar-rail-w)' : '',
        mobileOpen ? 'translate-x-0' : '-translate-x-full',
      ]"
      aria-label="Main navigation"
    >
      <!-- 56px, level with the top bar; in the rail the logo alone is centred. -->
      <div
        :class="
          cn('flex h-14 shrink-0 items-center gap-3 border-b px-4', rail && 'md:justify-center md:px-0')
        "
      >
        <span
          class="flex size-8 items-center justify-center rounded-md bg-brand text-caption font-semibold text-on-brand"
          aria-hidden="true"
        >
          {{ initials(user.orgName) }}
        </span>
        <span :class="cn('min-w-0 flex-1 truncate text-body-strong text-ink', hiddenInRail)">{{
          user.orgName
        }}</span>
      </div>

      <nav class="relative flex flex-1 flex-col gap-0.5 overflow-y-auto px-2 py-2" data-testid="main-nav">
        <RouterLink
          v-for="item in navigation"
          :key="item.routeName"
          :to="{ name: item.routeName }"
          :class="[navClass, isCurrent(item) && navActive]"
          :aria-current="isCurrent(item) ? 'page' : undefined"
          :aria-label="rail ? item.label : undefined"
          :title="rail ? item.label : undefined"
        >
          <component :is="item.icon" class="size-4 shrink-0" aria-hidden="true" /><span
            :class="hiddenInRail"
            >{{ item.label }}</span
          >
        </RouterLink>
      </nav>

      <div class="mx-2 flex flex-col gap-0.5 border-t py-2">
        <button
          type="button"
          :class="
            cn(
              'flex items-center gap-3 rounded-md px-3 py-1.5 text-body text-ink-muted hover:bg-surface-hover hover:text-ink max-md:hidden',
              rail && 'md:justify-center md:px-0',
            )
          "
          :aria-label="rail ? 'Expand sidebar' : 'Collapse sidebar'"
          :title="rail ? 'Expand sidebar' : 'Collapse sidebar'"
          data-testid="sidebar-toggle"
          @click="sidebar.toggle()"
        >
          <PanelLeftOpen v-if="rail" class="size-4 shrink-0" aria-hidden="true" />
          <PanelLeftClose v-else class="size-4 shrink-0" aria-hidden="true" />
          <span :class="hiddenInRail">Collapse</span>
        </button>
      </div>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col">
      <div class="flex min-h-0 flex-1 flex-col overflow-hidden" data-testid="page-sheet">
        <AppTopBar v-model:drawer-open="mobileOpen" />
        <!--
        Both scrollers are positioned (relative), so absolutely positioned descendants such as
        sr-only labels are placed inside them. Otherwise those labels are placed against the page,
        stretch the document past the window and scroll the whole shell, sidebar included.
      -->
        <main class="relative min-w-0 flex-1 overflow-y-auto bg-surface-page px-4 py-6 md:px-6">
          <slot />
        </main>
      </div>
    </div>
  </div>
</template>
