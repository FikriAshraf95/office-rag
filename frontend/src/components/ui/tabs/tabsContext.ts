import type { InjectionKey } from 'vue'

export type TabsVariant = 'underline' | 'segmented'

/** What Tabs shares with its list and triggers: the look, and how a trigger picks itself. */
export interface TabsContext {
  variant: TabsVariant
  select: (value: string) => void
}

export const tabsKey: InjectionKey<TabsContext> = Symbol('tabs')
