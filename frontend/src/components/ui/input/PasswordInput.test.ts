import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { PasswordInput } from '.'

// Every password field has an eye button that shows or hides what was typed.
describe('PasswordInput', () => {
  const field = (wrapper: ReturnType<typeof mount>) => wrapper.get('input')
  const eye = (wrapper: ReturnType<typeof mount>) => wrapper.get('button')

  it('hides the password until the eye is clicked, and hides it again on the next click', async () => {
    const wrapper = mount(PasswordInput)
    expect(field(wrapper).attributes('type')).toBe('password')
    expect(eye(wrapper).attributes('aria-label')).toBe('Show password')
    expect(eye(wrapper).attributes('aria-pressed')).toBe('false')

    await eye(wrapper).trigger('click')
    expect(field(wrapper).attributes('type')).toBe('text')
    expect(eye(wrapper).attributes('aria-label')).toBe('Hide password')
    expect(eye(wrapper).attributes('aria-pressed')).toBe('true')

    await eye(wrapper).trigger('click')
    expect(field(wrapper).attributes('type')).toBe('password')
  })

  it('works with v-model and keeps the typed text when toggled', async () => {
    const wrapper = mount(PasswordInput, {
      props: {
        modelValue: 'abc',
        'onUpdate:modelValue': (v: string | undefined) => wrapper.setProps({ modelValue: v }),
      },
    })
    await field(wrapper).setValue('Share-Pass-1111')
    expect(wrapper.props('modelValue')).toBe('Share-Pass-1111')
    await eye(wrapper).trigger('click')
    expect((field(wrapper).element as HTMLInputElement).value).toBe('Share-Pass-1111')
  })

  it('passes id, name, autocomplete, validation and event attributes to the input, not the wrapper', async () => {
    const onBlur = vi.fn()
    const wrapper = mount(PasswordInput, {
      attrs: {
        id: 'pw',
        name: 'password',
        autocomplete: 'new-password',
        maxlength: 128,
        required: true,
        'aria-invalid': true,
        'data-testid': 'pw-field',
        onBlur,
      },
    })
    const input = field(wrapper)
    expect(input.attributes('id')).toBe('pw')
    expect(input.attributes('name')).toBe('password')
    expect(input.attributes('autocomplete')).toBe('new-password')
    expect(input.attributes('maxlength')).toBe('128')
    expect(input.attributes('required')).toBeDefined()
    expect(input.attributes('aria-invalid')).toBe('true')
    expect(input.attributes('data-testid')).toBe('pw-field')
    expect(wrapper.element.getAttribute('id')).toBeNull()
    await input.trigger('blur')
    expect(onBlur).toHaveBeenCalledOnce()
  })

  it('does not submit the surrounding form when the eye is clicked', async () => {
    const onSubmit = vi.fn((e: Event) => e.preventDefault())
    const Host = {
      components: { PasswordInput },
      template: '<form @submit="onSubmit"><PasswordInput /></form>',
      setup: () => ({ onSubmit }),
    }
    const wrapper = mount(Host, { attachTo: document.body })
    await wrapper.get('button').trigger('click')
    expect(onSubmit).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('disables the eye with the field', () => {
    const wrapper = mount(PasswordInput, { attrs: { disabled: true } })
    expect(field(wrapper).attributes('disabled')).toBeDefined()
    expect(eye(wrapper).attributes('disabled')).toBeDefined()
  })

  it('keeps a caller class on the input and leaves room for the eye', () => {
    const wrapper = mount(PasswordInput, { attrs: { class: 'ring-danger' } })
    expect(field(wrapper).classes()).toContain('ring-danger')
    expect(field(wrapper).classes()).toContain('pr-10')
  })

  it('can be shown from outside through v-model:visible, and reports the eye clicks', async () => {
    const wrapper = mount(PasswordInput, {
      props: { visible: false, 'onUpdate:visible': (v: boolean) => wrapper.setProps({ visible: v }) },
    })
    await wrapper.setProps({ visible: true })
    expect(field(wrapper).attributes('type')).toBe('text')
    await eye(wrapper).trigger('click')
    expect(wrapper.props('visible')).toBe(false)
    expect(field(wrapper).attributes('type')).toBe('password')
  })
})
