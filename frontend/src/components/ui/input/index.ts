/** The field look shared by Input, Textarea and the Select trigger (design-system §1, §8). */
export const fieldClass =
  'rounded-md border border-border-input bg-surface text-body text-ink transition-colors placeholder:text-ink-subtle hover:border-border-strong disabled:opacity-50 aria-invalid:border-danger aria-invalid:hover:border-danger aria-invalid:focus-visible:outline-danger'

export { default as Input } from './Input.vue'
export { default as PasswordInput } from './PasswordInput.vue'
export { default as Textarea } from './Textarea.vue'
