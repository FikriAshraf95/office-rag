import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import FileDrop from './FileDrop.vue'

function choose(wrapper: ReturnType<typeof mount>, files: File[]) {
  const input = wrapper.find('input[type="file"]')
  Object.defineProperty(input.element, 'files', { value: files, configurable: true })
  return input.trigger('change')
}

describe('FileDrop', () => {
  it('emits every accepted file together', async () => {
    const wrapper = mount(FileDrop, { props: { accept: 'image/png,.pdf', maxBytes: 100 } })
    await choose(wrapper, [
      new File([new Uint8Array(10)], 'me.png', { type: 'image/png' }),
      new File([new Uint8Array(10)], 'policy.pdf', { type: 'application/pdf' }),
    ])
    const emitted = wrapper.emitted('files')?.[0]?.[0] as File[]
    expect(emitted.map((f) => f.name)).toEqual(['me.png', 'policy.pdf'])
    expect(wrapper.find('input[type="file"]').attributes('multiple')).toBeDefined()
  })

  it('refuses a file that is too large or of the wrong type, and still emits the rest', async () => {
    const wrapper = mount(FileDrop, { props: { accept: 'image/png', maxBytes: 100 } })
    await choose(wrapper, [
      new File([new Uint8Array(500)], 'big.png', { type: 'image/png' }),
      new File(['<svg/>'], 'x.svg', { type: 'image/svg+xml' }),
    ])
    expect(wrapper.text()).toContain('too large')
    expect(wrapper.text()).toContain("isn't allowed")
    expect(wrapper.emitted('files')).toBeUndefined()

    await choose(wrapper, [
      new File([new Uint8Array(500)], 'big.png', { type: 'image/png' }),
      new File([new Uint8Array(10)], 'ok.png', { type: 'image/png' }),
    ])
    expect((wrapper.emitted('files')?.[0]?.[0] as File[]).map((f) => f.name)).toEqual(['ok.png'])
  })

  it('shows progress while uploading and disables the button', () => {
    const wrapper = mount(FileDrop, { props: { progress: 0.42 } })
    expect(wrapper.find('button').text()).toBe('Uploading… 42%')
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })
})
