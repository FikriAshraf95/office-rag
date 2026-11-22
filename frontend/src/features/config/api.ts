import { http } from '@/api/http'
import type { components } from '@/api/schema'
import configFixture from '@/fixtures/config.json'

export type ConfigOut = components['schemas']['ConfigOut']
export type DemoUserOut = components['schemas']['DemoUserOut']
export type MeOut = components['schemas']['MeOut']

const useFixtures = import.meta.env.VITE_USE_FIXTURES === '1'

export const configApi = {
  /** `GET /config`: public, sent without `X-Demo-User` (SPEC-08 §3). */
  async get(): Promise<ConfigOut> {
    if (useFixtures) return configFixture
    return (await http.get<ConfigOut>('/config')).data
  },

  /** `GET /me`: the current demo user and groups. */
  async me(): Promise<MeOut> {
    if (useFixtures) {
      const user = configFixture.demoUsers[0]
      if (user) return user
    }
    return (await http.get<MeOut>('/me')).data
  },
}
