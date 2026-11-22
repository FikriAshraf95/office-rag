import type { InjectionKey } from 'vue'

/** Provided by TooltipProvider, so a Tooltip knows a provider is mounted above it. */
export const tooltipHostKey: InjectionKey<true> = Symbol('tooltip-host')
