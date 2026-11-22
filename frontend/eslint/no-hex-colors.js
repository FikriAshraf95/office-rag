// Flags hex colour literals (#fff, #004d70, #00000080) anywhere in a .vue or .ts file, including
// <style> blocks, which ESLint's parsers don't otherwise see (SPEC-21 §1, §11 check 6).
// Colours come from design tokens: var(--brand), bg-brand, …
const HEX = /(?<![\w&/])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![\w-])/g

/** @type {import('eslint').Rule.RuleModule} */
export default {
  meta: {
    type: 'problem',
    docs: { description: 'Disallow hex colour literals; use design tokens.' },
    schema: [],
    messages: { hex: 'Raw colour {{value}}: use a design token from tokens.css instead.' },
  },
  create(context) {
    return {
      Program() {
        const text = context.sourceCode.text
        for (const match of text.matchAll(HEX)) {
          const start = context.sourceCode.getLocFromIndex(match.index)
          const end = context.sourceCode.getLocFromIndex(match.index + match[0].length)
          context.report({ loc: { start, end }, messageId: 'hex', data: { value: match[0] } })
        }
      },
    }
  },
}
