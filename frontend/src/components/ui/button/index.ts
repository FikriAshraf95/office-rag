import { cva, type VariantProps } from 'class-variance-authority'

export { default as Button } from './Button.vue'

/** Design-system §10: primary (one per view), secondary, ghost (toolbars), danger (confirmations only). */
export const buttonVariants = cva(
  'inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-md text-body-strong transition-[background-color,box-shadow,transform] active:translate-y-px disabled:cursor-not-allowed disabled:border-transparent disabled:bg-surface-sunken disabled:text-ink-muted disabled:opacity-60 disabled:shadow-none [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        primary: 'bg-brand text-on-brand shadow-sm hover:bg-brand-hover',
        secondary: 'border bg-surface text-ink shadow-sm hover:bg-surface-sunken',
        ghost: 'text-ink hover:bg-surface-hover',
        danger: 'bg-danger-fill text-on-danger shadow-sm hover:opacity-90',
        link: 'text-brand-ink underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-(--control-h) px-3',
        sm: 'h-(--control-h-sm) px-2',
        icon: 'size-(--control-h)',
      },
    },
    defaultVariants: { variant: 'secondary', size: 'default' },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>
