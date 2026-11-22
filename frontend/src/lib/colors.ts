/** The label palette (design-system §2.1). Data stores the colour *name*, never a hex value. */
export const labelColors = [
  'grey',
  'red',
  'orange',
  'amber',
  'green',
  'teal',
  'cyan',
  'blue',
  'indigo',
  'purple',
  'pink',
  'brown',
] as const

export type LabelColor = (typeof labelColors)[number]

/** A stable label colour for an ID: the same user always gets the same avatar colour. Grey is skipped. */
export function colorForId(id: string): LabelColor {
  let hash = 0
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0
  const palette = labelColors.slice(1)
  return palette[hash % palette.length] ?? 'blue'
}

/** Tailwind classes for a label fill and its text colour. Spelled out so Tailwind can see them. */
export const labelClasses: Record<LabelColor, string> = {
  grey: 'bg-label-grey text-on-label-grey',
  red: 'bg-label-red text-on-label-red',
  orange: 'bg-label-orange text-on-label-orange',
  amber: 'bg-label-amber text-on-label-amber',
  green: 'bg-label-green text-on-label-green',
  teal: 'bg-label-teal text-on-label-teal',
  cyan: 'bg-label-cyan text-on-label-cyan',
  blue: 'bg-label-blue text-on-label-blue',
  indigo: 'bg-label-indigo text-on-label-indigo',
  purple: 'bg-label-purple text-on-label-purple',
  pink: 'bg-label-pink text-on-label-pink',
  brown: 'bg-label-brown text-on-label-brown',
}

/** Tailwind classes for a soft tint and its ink (StatusPill, design-system §10). */
export const labelSoftClasses: Record<LabelColor, string> = {
  grey: 'bg-label-grey-soft text-on-label-grey-soft',
  red: 'bg-label-red-soft text-on-label-red-soft',
  orange: 'bg-label-orange-soft text-on-label-orange-soft',
  amber: 'bg-label-amber-soft text-on-label-amber-soft',
  green: 'bg-label-green-soft text-on-label-green-soft',
  teal: 'bg-label-teal-soft text-on-label-teal-soft',
  cyan: 'bg-label-cyan-soft text-on-label-cyan-soft',
  blue: 'bg-label-blue-soft text-on-label-blue-soft',
  indigo: 'bg-label-indigo-soft text-on-label-indigo-soft',
  purple: 'bg-label-purple-soft text-on-label-purple-soft',
  pink: 'bg-label-pink-soft text-on-label-pink-soft',
  brown: 'bg-label-brown-soft text-on-label-brown-soft',
}

/** Up to two initials: "Mei Lin Tan" → "MT", "admin" → "AD". */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase()
  return (parts[0]![0]! + parts[parts.length - 1]![0]!).toUpperCase()
}

/** Tailwind classes for an SVG fill in a label colour (Gantt bars). */
export const labelFillClasses: Record<LabelColor, string> = {
  grey: 'fill-label-grey',
  red: 'fill-label-red',
  orange: 'fill-label-orange',
  amber: 'fill-label-amber',
  green: 'fill-label-green',
  teal: 'fill-label-teal',
  cyan: 'fill-label-cyan',
  blue: 'fill-label-blue',
  indigo: 'fill-label-indigo',
  purple: 'fill-label-purple',
  pink: 'fill-label-pink',
  brown: 'fill-label-brown',
}
