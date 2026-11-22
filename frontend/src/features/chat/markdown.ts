import MarkdownIt, { type StateCore, type Token } from 'markdown-it'

/**
 * Answer markdown (SPEC-07 §5.3): `html: false`, no linkify, no typographer. An extra core rule
 * turns `[n]`, `[n][m]` and `[n, m]` into one citation button per number, but only for numbers in
 * `1…sources.length`; any other number stays plain text. The output still goes through
 * `sanitizeAnswer` (SafeHtml) before it reaches the DOM.
 */
export interface CiteSource {
  n: number
  title: string
}

const GROUP = /(?:\[\d+(?:\s*,\s*\d+)*\])+/g

function citationRule(sources: () => CiteSource[]) {
  return (state: StateCore) => {
    const list = sources()
    for (const block of state.tokens) {
      if (block.type !== 'inline' || !block.children) continue
      const out: Token[] = []
      for (const child of block.children) {
        if (child.type !== 'text') {
          out.push(child)
          continue
        }
        split(state, child.content, list, out, child.level)
      }
      block.children = out
    }
  }
}

function text(state: StateCore, content: string, level: number): Token {
  const t = new state.Token('text', '', 0)
  t.content = content
  t.level = level
  return t
}

function split(state: StateCore, content: string, sources: CiteSource[], out: Token[], level: number) {
  let last = 0
  for (const match of content.matchAll(GROUP)) {
    const start = match.index ?? 0
    if (start > last) out.push(text(state, content.slice(last, start), level))
    for (const num of match[0].match(/\d+/g) ?? []) {
      const n = Number(num)
      const source = sources.find((s) => s.n === n)
      if (!source) {
        out.push(text(state, `[${num}]`, level))
        continue
      }
      const button = new state.Token('html_inline', '', 0)
      const label = state.md.utils.escapeHtml(`Source ${n}: ${source.title}`)
      button.content = `<button class="citation" data-cite="${n}" aria-label="${label}">${n}</button>`
      button.level = level
      out.push(button)
    }
    last = start + match[0].length
  }
  if (last < content.length) out.push(text(state, content.slice(last), level))
}

/** Renders answer text to (unsanitized) HTML for the given sources. */
export function createAnswerRenderer() {
  let current: CiteSource[] = []
  const md = new MarkdownIt({ html: false, linkify: false, typographer: false })
  md.core.ruler.push(
    'citations',
    citationRule(() => current),
  )
  return (markdown: string, sources: CiteSource[]): string => {
    current = sources
    return md.render(markdown)
  }
}

export const renderAnswer = createAnswerRenderer()

const plain = new MarkdownIt({ html: false, linkify: false, typographer: false })
/** Markdown without citations (chunk text with tables in the viewer). Also needs sanitizing. */
export function renderMarkdown(markdown: string): string {
  return plain.render(markdown)
}
