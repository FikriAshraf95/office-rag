import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

/** Routes (SPEC-07 §4). Each page is its own chunk. */
export const routes: RouteRecordRaw[] = [
  { path: '/', redirect: { name: 'chat' } },
  { path: '/chat', name: 'chat', component: () => import('@/features/chat/ChatPage.vue') },
  {
    path: '/documents',
    name: 'documents',
    component: () => import('@/features/documents/DocumentsPage.vue'),
  },
  {
    path: '/documents/:id',
    name: 'document',
    component: () => import('@/features/documents/DocumentDetailPage.vue'),
  },
  { path: '/usage', name: 'usage', component: () => import('@/features/usage/UsagePage.vue') },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('./NotFoundPage.vue') },
]

export function createAppRouter() {
  return createRouter({ history: createWebHistory(), routes })
}

export const router = createAppRouter()
