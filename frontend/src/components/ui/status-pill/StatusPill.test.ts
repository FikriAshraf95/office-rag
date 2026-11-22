import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StatusPill from './StatusPill.vue'

describe('StatusPill', () => {
  it('shows the label with a hidden dot on the soft tint of its colour', () => {
    const w = mount(StatusPill, { props: { color: 'red', label: 'Stuck' } })
    expect(w.text()).toBe('Stuck')
    expect(w.classes()).toContain('bg-label-red-soft')
    expect(w.find('[aria-hidden="true"]').exists()).toBe(true)
  })

  it('falls back to grey for an unknown colour', () => {
    expect(mount(StatusPill, { props: { color: 'nope', label: 'x' } }).classes()).toContain(
      'bg-label-grey-soft',
    )
  })
})
