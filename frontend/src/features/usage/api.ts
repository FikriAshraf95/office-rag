import { http } from '@/api/http'
import type { components } from '@/api/schema'
import usageFixture from '@/fixtures/usage.json'

export type UsageSummary = components['schemas']['UsageSummaryOut']
export type UsageByModel = components['schemas']['UsageByModelOut']

const useFixtures = import.meta.env.VITE_USE_FIXTURES === '1'

export const usageApi = {
  /** `GET /usage/summary`: tokens and cost by model and purpose, plus the latest balances. */
  async summary(): Promise<UsageSummary> {
    if (useFixtures) return usageFixture
    return (await http.get<UsageSummary>('/usage/summary', { silent: true })).data
  },
}
