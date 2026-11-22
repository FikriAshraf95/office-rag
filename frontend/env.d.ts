/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** "1" makes features/<name>/api.ts return fixtures from src/fixtures/ (SPEC-07 §10). */
  readonly VITE_USE_FIXTURES?: string
}
