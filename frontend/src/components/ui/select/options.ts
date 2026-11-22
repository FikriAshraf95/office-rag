import { Comment, Fragment, Text, type VNode } from 'vue'

export interface SelectOption {
  value: unknown
  label: string
  disabled: boolean
  group?: string
}

function text(children: unknown): string {
  if (typeof children === 'string') return children
  if (!Array.isArray(children)) return ''
  return children
    .map((c: VNode | string) => {
      if (typeof c === 'string') return c
      if (c.type === Comment) return ''
      return text(c.children)
    })
    .join('')
}

const isOff = (v: unknown) => v === undefined || v === null || v === false

/** Reads `<option>` and `<optgroup>` slot content, through v-for and v-if fragments, into a flat list. */
export function readOptions(nodes: VNode[] | undefined, group?: string): SelectOption[] {
  const options: SelectOption[] = []
  for (const node of nodes ?? []) {
    if (node.type === Comment || node.type === Text) continue
    if (node.type === Fragment) {
      options.push(...readOptions(node.children as VNode[], group))
    } else if (node.type === 'optgroup') {
      options.push(...readOptions(node.children as VNode[], String(node.props?.label ?? '')))
    } else if (node.type === 'option') {
      const label = text(node.children).trim()
      options.push({
        value: node.props && 'value' in node.props ? node.props.value : label,
        label,
        disabled: !isOff(node.props?.disabled),
        group,
      })
    }
  }
  return options
}

/** The option a model value shows. As with a native select, numbers match their string form; null is the empty option. */
export function matchOption(options: SelectOption[], value: unknown): number {
  const key = String(value ?? '')
  return options.findIndex((o) => String(o.value ?? '') === key)
}
