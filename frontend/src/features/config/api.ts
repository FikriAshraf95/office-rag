import { http } from '@/api/http'
import type { components } from '@/api/schema'
import configJson from '@/fixtures/config.json'

export type ConfigOut = components['schemas']['ConfigOut']
export type DemoUserOut = components['schemas']['DemoUserOut']
export type MeOut = components['schemas']['MeOut']

/** The demo config fixture, typed (JSON imports widen `authMode` to string). */
export const configFixture = configJson as ConfigOut

const useFixtures = import.meta.env.VITE_USE_FIXTURES === '1'

export const configApi = {
  /** `GET /config`: public, sent without `X-Demo-User` (SPEC-08 §3). */
  async get(): Promise<ConfigOut> {
    if (useFixtures) return configFixture
    return (await http.get<ConfigOut>('/config')).data
  },

  /** `GET /me`: the current user, groups and admin flag. `silent`: the caller shows its own message. */
  async me(options: { silent?: boolean } = {}): Promise<MeOut> {
    if (useFixtures) {
      const user = configFixture.demoUsers[0]
      if (user) return { ...user, isAdmin: true }
    }
    return (await http.get<MeOut>('/me', { silent: options.silent })).data
  },
}

export const authApi = {
  /** `POST /auth/login` (password mode): sets the HttpOnly session cookie. Errors are shown by the form. */
  async login(username: string, password: string): Promise<MeOut> {
    return (await http.post<MeOut>('/auth/login', { username, password }, { silent: true })).data
  },

  /** `POST /auth/logout`: clears the session cookie. */
  async logout(): Promise<void> {
    await http.post('/auth/logout', undefined, { silent: true })
  },
}
