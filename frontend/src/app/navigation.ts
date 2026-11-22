import type { Component } from 'vue'
import { ChartColumn, FileText, MessageSquare } from 'lucide-vue-next'

/** The sidebar entries (SPEC-07 §3, §4): Chat, Documents, Usage. */
export interface NavItem {
  label: string
  /** Route name; must exist in router.ts. */
  routeName: string
  /** Other routes that belong under this entry, so it stays highlighted on them (e.g. a detail page). */
  alsoActiveFor?: string[]
  icon: Component
}

export const navigation: NavItem[] = [
  { label: 'Chat', routeName: 'chat', icon: MessageSquare },
  { label: 'Documents', routeName: 'documents', alsoActiveFor: ['document'], icon: FileText },
  { label: 'Usage', routeName: 'usage', icon: ChartColumn },
]
