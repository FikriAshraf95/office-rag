import { flushPromises } from '@vue/test-utils'

// Test helpers for Select: its list lives in a portal and opens from the keyboard or a pointer. jsdom lacks the pointer
// capture and scrolling calls the popup makes.
function prepareDom() {
  const proto = Element.prototype as unknown as Record<string, unknown>
  for (const name of ['hasPointerCapture', 'setPointerCapture', 'releasePointerCapture', 'scrollIntoView']) {
    proto[name] ??= () => false
  }
}

const items = () => [...document.body.querySelectorAll<HTMLElement>('[role="option"]')]

async function open(trigger: Element) {
  prepareDom()
  trigger.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
  await flushPromises()
}

/** Opens a Select and picks the option with this value. */
export async function pickOption(trigger: Element, value: string) {
  await open(trigger)
  const item = items().find((o) => o.dataset.value === value)
  if (!item) throw new Error(`No option "${value}" in: ${items().map((o) => o.dataset.value)}`)
  item.dispatchEvent(new MouseEvent('pointerup', { bubbles: true }))
  await flushPromises()
}

/** Opens a Select, reads its option labels and closes it. */
export async function optionLabels(trigger: Element) {
  await open(trigger)
  const labels = items().map((o) => o.textContent?.trim() ?? '')
  document.activeElement?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
  await flushPromises()
  return labels
}
