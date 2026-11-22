import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import noHexColors from './eslint/no-hex-colors.js'

// SPEC-07 §3: no v-html (user HTML renders only through SafeHtml.vue) and no raw colours (every
// colour comes from src/styles/tokens.css). SafeHtml.vue is the single allowed v-html.
export default defineConfigWithVueTs(
  { name: 'app/files', files: ['**/*.{ts,mts,tsx,vue}'] },
  {
    name: 'app/ignores',
    ignores: ['eslint/**', 'dist/**', 'coverage/**', 'src/api/schema.d.ts'],
  },
  pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,
  {
    name: 'app/rules',
    plugins: { local: { rules: { 'no-hex-colors': noHexColors } } },
    rules: {
      'vue/no-v-html': 'error',
      'local/no-hex-colors': 'error',
      'vue/multi-word-component-names': 'off',
      // Optional TypeScript props are undefined by design.
      'vue/require-default-prop': 'off',
      '@typescript-eslint/no-explicit-any': 'error',
    },
  },
  {
    name: 'app/safe-html',
    files: ['src/components/common/SafeHtml.vue'],
    rules: { 'vue/no-v-html': 'off' },
  },
  skipFormatting,
)
