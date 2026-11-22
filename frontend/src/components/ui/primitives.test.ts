import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { defineComponent, ref } from 'vue'
import { Banner } from './banner'
import { Skeleton, SkeletonRows } from './skeleton'
import { Switch } from './switch'
import { DataTable } from './table'
import { Tabs, TabsList, TabsTrigger } from './tabs'
import { Tooltip } from './tooltip'

describe('Tabs', () => {
  const Harness = defineComponent({
    components: { Tabs, TabsList, TabsTrigger },
    props: { variant: { type: String, default: 'underline' } },
    setup: () => ({ tab: ref('a') }),
    template: `<Tabs v-model="tab" :variant="variant"><TabsList aria-label="Sections">
      <TabsTrigger value="a" data-testid="ta">A</TabsTrigger><TabsTrigger value="b" data-testid="tb">B</TabsTrigger>
    </TabsList><p data-testid="current">{{ tab }}</p></Tabs>`,
  })

  it('keeps tab semantics and selects on click', async () => {
    const w = mount(Harness, { attachTo: document.body })
    expect(w.findAll('[role="tab"]')).toHaveLength(2)
    expect(w.get('[role="tablist"]').attributes('aria-label')).toBe('Sections')
    expect(w.get('[data-testid="ta"]').attributes('aria-selected')).toBe('true')
    await w.get('[data-testid="tb"]').trigger('click')
    expect(w.get('[data-testid="current"]').text()).toBe('b')
    expect(w.get('[data-testid="tb"]').attributes('aria-selected')).toBe('true')
    w.unmount()
  })

  it('segmented sits on a sunken pill group', () => {
    const w = mount(Harness, { props: { variant: 'segmented' } })
    expect(w.get('[role="tablist"]').classes()).toContain('bg-surface-sunken')
  })
})

describe('Skeleton', () => {
  it('rows announce a status with sr-only text', () => {
    const w = mount(SkeletonRows, { props: { rows: 2, cols: 3 } })
    expect(w.attributes('role')).toBe('status')
    expect(w.get('.sr-only').text()).toBe('Loading…')
    expect(w.findAllComponents(Skeleton)).toHaveLength(6)
  })
})

describe('Banner', () => {
  it('danger is an alert, info is not', () => {
    expect(mount(Banner, { props: { tone: 'danger' }, slots: { default: 'Bad' } }).attributes('role')).toBe(
      'alert',
    )
    const info = mount(Banner, {
      props: { tone: 'info' },
      slots: { default: 'Note', action: '<button>Go</button>' },
    })
    expect(info.attributes('role')).toBeUndefined()
    expect(info.classes()).toContain('bg-info-soft')
    expect(info.text()).toContain('Go')
  })
})

describe('DataTable', () => {
  it('renders a real table and passes attributes to it', () => {
    const w = mount(DataTable, {
      attrs: { 'data-testid': 'things' },
      slots: { default: '<thead><tr><th>Name</th></tr></thead><tbody><tr><td>x</td></tr></tbody>' },
    })
    expect(w.get('table').attributes('data-testid')).toBe('things')
    expect(w.findAll('th')).toHaveLength(1)
  })
})

describe('Switch', () => {
  it('toggles its model', async () => {
    const w = mount(Switch, { props: { 'aria-label': 'On', modelValue: false } })
    expect(w.get('[role="switch"]').attributes('aria-checked')).toBe('false')
    await w.get('[role="switch"]').trigger('click')
    expect(w.emitted('update:modelValue')?.[0]).toEqual([true])
  })
})

describe('Tooltip', () => {
  it('renders just the trigger when there is no text', async () => {
    const w = mount(Tooltip, { slots: { default: '<button>Go</button>' } })
    await flushPromises()
    expect(w.find('button').exists()).toBe(true)
    expect(w.find('span').exists()).toBe(false)
  })

  it('wraps the trigger without its own provider mounted above', async () => {
    const w = mount(Tooltip, { props: { text: 'Why' }, slots: { default: '<button disabled>Go</button>' } })
    await flushPromises()
    expect(w.find('button').exists()).toBe(true)
  })
})
