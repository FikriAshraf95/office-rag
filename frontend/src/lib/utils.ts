import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Merges class lists, letting later Tailwind classes win (shadcn-vue convention). */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

/** "1.5 MB", "12 KB", "300 B" (copied from Office Suite `features/files/api.ts`). */
export function formatBytes(bytes: number): string {
  const round = (n: number) => Math.round(n * 10) / 10
  if (bytes >= 1024 ** 3) return `${round(bytes / 1024 ** 3)} GB`
  if (bytes >= 1024 ** 2) return `${round(bytes / 1024 ** 2)} MB`
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`
  return `${bytes} B`
}
