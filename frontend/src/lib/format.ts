/** Date formatting in the organisation format and timezone (Asia/Kuala_Lumpur, SPEC-07 §3). */
export type DateFormat = 'dd/MM/yyyy' | 'MM/dd/yyyy' | 'yyyy-MM-dd'

export interface DateSettings {
  dateFormat?: string | null
  timezone?: string | null
}

const fallback: Required<{ [K in keyof DateSettings]: string }> = {
  dateFormat: 'dd/MM/yyyy',
  timezone: 'Asia/Kuala_Lumpur',
}

function parts(date: Date, timezone: string): Record<string, string> {
  const fmt = new Intl.DateTimeFormat('en-GB', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
  return Object.fromEntries(fmt.formatToParts(date).map((p) => [p.type, p.value]))
}

/** "02/11/2026" for dd/MM/yyyy. */
export function formatDate(value: string | Date, settings: DateSettings = {}): string {
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  const p = parts(date, settings.timezone ?? fallback.timezone)
  switch ((settings.dateFormat ?? fallback.dateFormat) as DateFormat) {
    case 'MM/dd/yyyy':
      return `${p.month}/${p.day}/${p.year}`
    case 'yyyy-MM-dd':
      return `${p.year}-${p.month}-${p.day}`
    default:
      return `${p.day}/${p.month}/${p.year}`
  }
}

/** "02/11/2026 09:30". */
export function formatDateTime(value: string | Date, settings: DateSettings = {}): string {
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  const p = parts(date, settings.timezone ?? fallback.timezone)
  return `${formatDate(date, settings)} ${p.hour}:${p.minute}`
}

/** "just now", "5 minutes ago", "3 hours ago", "2 days ago"; older than a week → the date. */
export function formatRelative(
  value: string | Date,
  now: Date = new Date(),
  settings: DateSettings = {},
): string {
  const date = typeof value === 'string' ? new Date(value) : value
  const seconds = Math.round((now.getTime() - date.getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days} day${days === 1 ? '' : 's'} ago`
  return formatDate(date, settings)
}
