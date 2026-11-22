import DOMPurify from 'dompurify'

/**
 * The answer allowlist (SPEC-07 §3, §5.3). Model output is rendered by markdown-it with
 * `html: false`, then passes through here before SafeHtml. `button` survives only as a citation
 * (`class="citation"` + `data-cite` + `aria-label`), links only with an http, https or mailto
 * `href`, and nothing else (styles, handlers, images, iframes).
 */
export const ALLOWED_TAGS = [
  'p',
  'br',
  'strong',
  'em',
  'code',
  'pre',
  'ul',
  'ol',
  'li',
  'table',
  'thead',
  'tbody',
  'tr',
  'th',
  'td',
  'h3',
  'h4',
  'blockquote',
  'a',
  'sup',
  'button',
]
export const ALLOWED_ATTR = ['href', 'class', 'data-cite', 'aria-label']

const CITE = /^[1-9]\d*$/

let hooked = false

function install(): void {
  // A button that isn't a well-formed citation is replaced by its text.
  DOMPurify.addHook('uponSanitizeElement', (node, data) => {
    if (data.tagName !== 'button' || !(node instanceof Element)) return
    const ok =
      node.getAttribute('class') === 'citation' &&
      CITE.test(node.getAttribute('data-cite') ?? '') &&
      (node.getAttribute('aria-label') ?? '') !== ''
    if (!ok) node.replaceWith(node.ownerDocument.createTextNode(node.textContent ?? ''))
  })
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'BUTTON') {
      // Citation buttons keep exactly class, data-cite and aria-label.
      for (const name of node.getAttributeNames()) {
        if (!['class', 'data-cite', 'aria-label'].includes(name)) node.removeAttribute(name)
      }
      node.setAttribute('type', 'button')
      return
    }
    // Everything else drops the citation attributes; a link keeps only href.
    node.removeAttribute('class')
    node.removeAttribute('data-cite')
    node.removeAttribute('aria-label')
    if (node.tagName === 'A') {
      if (!node.getAttribute('href')) node.removeAttribute('href')
      // Links always open safely in a new tab.
      node.setAttribute('target', '_blank')
      node.setAttribute('rel', 'noopener noreferrer nofollow')
    }
  })
  hooked = true
}

export function sanitizeAnswer(html: string): string {
  if (!hooked) install()
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOWED_URI_REGEXP: /^(?:https?:|mailto:)/i,
  })
}
