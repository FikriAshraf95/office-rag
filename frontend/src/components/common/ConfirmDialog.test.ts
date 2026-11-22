import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { computed, defineComponent, ref } from 'vue'
import ConfirmDialog from './ConfirmDialog.vue'

// The dialog closes when it is confirmed. Pages that keep "what to delete" in the same state that
// opens the dialog (open = target !== null) clear it on close, so `confirm` must reach them first:
// before this was fixed, deleting a file share did nothing and sent no request.
const seen = vi.fn<(target: string | null) => void>()

const Host = defineComponent({
  components: { ConfirmDialog },
  setup() {
    const target = ref<string | null>('pack.zip')
    const open = computed({
      get: () => target.value !== null,
      set: (value) => {
        if (!value) target.value = null
      },
    })
    return { open, confirm: () => seen(target.value) }
  },
  template: `<ConfirmDialog v-model:open="open" title="Delete this link?" confirm-label="Delete" danger @confirm="confirm" />`,
})

describe('ConfirmDialog', () => {
  let wrapper: VueWrapper
  const q = (selector: string) => document.body.querySelector<HTMLElement>(selector)
  const button = (label: string) =>
    [...document.body.querySelectorAll('button')].find((b) => b.textContent?.trim() === label)

  async function show() {
    wrapper = mount(Host, { attachTo: document.body })
    await flushPromises()
  }

  afterEach(() => {
    wrapper.unmount()
    seen.mockClear()
    document.body.innerHTML = ''
  })

  it('emits confirm while the host still holds its target, then closes', async () => {
    await show()
    expect(q('[role="alertdialog"]')).not.toBeNull()
    button('Delete')!.click()
    await flushPromises()
    expect(seen).toHaveBeenCalledExactlyOnceWith('pack.zip')
    expect(q('[role="alertdialog"]')).toBeNull()
  })

  it('does not emit confirm on cancel, and still closes', async () => {
    await show()
    button('Cancel')!.click()
    await flushPromises()
    expect(seen).not.toHaveBeenCalled()
    expect(q('[role="alertdialog"]')).toBeNull()
  })
})
