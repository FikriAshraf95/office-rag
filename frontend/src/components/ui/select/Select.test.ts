import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { defineComponent, h, nextTick, ref } from 'vue'
import { Select } from '.'
import { matchOption, readOptions } from './options'
import { optionLabels, pickOption } from './testing'

const option = (value: unknown, text: string, disabled?: boolean) => h('option', { value, disabled }, text)

function host(initial: string | undefined, children: () => ReturnType<typeof h>[]) {
  const model = ref(initial)
  const Host = defineComponent(
    () => () =>
      h(
        Select,
        {
          modelValue: model.value,
          'onUpdate:modelValue': (v?: string) => (model.value = v),
          'aria-label': 'Pick',
        },
        children,
      ),
  )
  return { model, wrapper: mount(Host, { attachTo: document.body }) }
}

describe('readOptions', () => {
  it('reads options through fragments and groups, with their labels and disabled state', () => {
    const nodes = [option('', 'None', true), h('optgroup', { label: 'Teams' }, [option('t1', 'Team 1')])]
    expect(readOptions(nodes)).toEqual([
      { value: '', label: 'None', disabled: true, group: undefined },
      { value: 't1', label: 'Team 1', disabled: false, group: 'Teams' },
    ])
  })

  it('uses the text as the value when an option has none', () => {
    expect(readOptions([h('option', 'Plain')])[0]?.value).toBe('Plain')
  })
})

describe('matchOption', () => {
  const options = readOptions([option('', 'Any'), option(5, 'Five')])

  it('treats null and undefined as the empty option, and numbers as their text', () => {
    expect(matchOption(options, null)).toBe(0)
    expect(matchOption(options, undefined)).toBe(0)
    expect(matchOption(options, '5')).toBe(1)
    expect(matchOption(options, 'x')).toBe(-1)
  })
})

describe('Select', () => {
  it('shows the chosen label, forwards attributes to the trigger and writes the option value', async () => {
    const { model, wrapper } = host('', () => [option('', 'Any team'), option('t1', 'Team 1')])
    const trigger = wrapper.get('[role="combobox"]')
    expect(trigger.attributes('aria-label')).toBe('Pick')
    expect(trigger.text()).toBe('Any team')
    await pickOption(trigger.element, 't1')
    expect(model.value).toBe('t1')
    expect(wrapper.get('[role="combobox"]').text()).toBe('Team 1')
    wrapper.unmount()
  })

  it('can go back to an option with an empty value', async () => {
    const { model, wrapper } = host('t1', () => [option('', 'Any team'), option('t1', 'Team 1')])
    await pickOption(wrapper.get('[role="combobox"]').element, '')
    expect(model.value).toBe('')
    wrapper.unmount()
  })

  it('follows options that change after mounting', async () => {
    const names = ref(['One'])
    const { wrapper } = host('One', () => names.value.map((n) => option(n, n)))
    names.value = ['One', 'Two']
    await nextTick()
    expect(await optionLabels(wrapper.get('[role="combobox"]').element)).toEqual(['One', 'Two'])
    wrapper.unmount()
  })
})
