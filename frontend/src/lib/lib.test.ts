import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SafeHtml from '@/components/common/SafeHtml.vue'
import { colorForId, initials, labelClasses } from './colors'
import { formatDate, formatDateTime, formatRelative } from './format'
import { sanitizeAnswer } from './sanitize'
import { applyTheme, readStoredTheme, THEME_STORAGE_KEY } from './theme'

describe('format', () => {
  const instant = '2026-11-02T01:30:00Z' // 09:30 in Kuala Lumpur

  it('formats dates in the organisation format and timezone', () => {
    expect(formatDate(instant)).toBe('02/11/2026')
    expect(formatDate(instant, { dateFormat: 'MM/dd/yyyy' })).toBe('11/02/2026')
    expect(formatDate(instant, { dateFormat: 'yyyy-MM-dd' })).toBe('2026-11-02')
    expect(formatDate('2026-11-01T20:00:00Z', { timezone: 'Asia/Kuala_Lumpur' })).toBe('02/11/2026')
    expect(formatDate('2026-11-01T20:00:00Z', { timezone: 'UTC' })).toBe('01/11/2026')
    expect(formatDate('not a date')).toBe('')
  })

  it('formats date and time on a 24-hour clock', () => {
    expect(formatDateTime(instant)).toBe('02/11/2026 09:30')
  })

  it('formats relative times', () => {
    const now = new Date('2026-11-02T12:00:00Z')
    expect(formatRelative('2026-11-02T11:59:30Z', now)).toBe('just now')
    expect(formatRelative('2026-11-02T11:59:00Z', now)).toBe('1 minute ago')
    expect(formatRelative('2026-11-02T09:00:00Z', now)).toBe('3 hours ago')
    expect(formatRelative('2026-10-31T12:00:00Z', now)).toBe('2 days ago')
    expect(formatRelative('2026-10-01T12:00:00Z', now)).toBe('01/10/2026')
  })
})

describe('colors', () => {
  it('gives an ID the same non-grey label colour every time', () => {
    const id = '01920000-0000-7000-8000-000000000001'
    expect(colorForId(id)).toBe(colorForId(id))
    expect(colorForId(id)).not.toBe('grey')
    expect(labelClasses[colorForId(id)]).toMatch(/^bg-label-\w+ text-on-label-\w+$/)
  })

  it('makes up to two initials', () => {
    expect(initials('Mei Lin Tan')).toBe('MT')
    expect(initials('admin')).toBe('AD')
    expect(initials('  ')).toBe('?')
  })
})

describe('sanitize (SPEC-07 §3 answer allowlist, §11 check 2)', () => {
  it('executes nothing from <img onerror> or <script>', () => {
    const dirty =
      '<p>Hi <img src=x onerror="alert(1)"><script>alert(2)</script><a href="javascript:alert(3)">x</a></p>'
    const clean = sanitizeAnswer(dirty)
    expect(clean).not.toMatch(/onerror|<script|javascript:|<img/i)
    expect(clean).toContain('<p>Hi ')
  })

  it('keeps answer formatting and tables, and makes links open safely', () => {
    const clean = sanitizeAnswer(
      '<h3>T</h3><table><thead><tr><th>a</th></tr></thead><tbody><tr><td>1</td></tr></tbody></table>' +
        '<strong>bold</strong> <sup>2</sup> <a href="https://example.test" class="x" title="t">link</a>',
    )
    expect(clean).toContain(
      '<table><thead><tr><th>a</th></tr></thead><tbody><tr><td>1</td></tr></tbody></table>',
    )
    expect(clean).toContain('<strong>bold</strong> <sup>2</sup>')
    expect(clean).toContain('href="https://example.test"')
    expect(clean).toContain('rel="noopener noreferrer nofollow"')
    expect(clean).not.toMatch(/class="x"|title=/)
  })

  it('keeps a citation button with exactly class, data-cite and aria-label', () => {
    const clean = sanitizeAnswer(
      '<button class="citation" data-cite="1" aria-label="Source 1: Handbook" onclick="a()" style="x:y">1</button>',
    )
    expect(clean).toContain('class="citation"')
    expect(clean).toContain('data-cite="1"')
    expect(clean).toContain('aria-label="Source 1: Handbook"')
    expect(clean).not.toMatch(/onclick|style/)
  })

  it('turns any other button into plain text', () => {
    expect(sanitizeAnswer('<p><button class="evil">go</button></p>')).toBe('<p>go</p>')
    expect(sanitizeAnswer('<button class="citation" aria-label="x">1</button>')).toBe('1')
  })

  it('drops tags outside the allowlist and citation attributes elsewhere', () => {
    const clean = sanitizeAnswer(
      '<span class="citation" data-cite="1">s</span><h1>H</h1><iframe src="x"></iframe>',
    )
    expect(clean).not.toMatch(/<span|<h1|<iframe|data-cite|class=/)
  })

  it('SafeHtml renders only the sanitised HTML', () => {
    const wrapper = mount(SafeHtml, { props: { html: '<em>ok</em><img src=x onerror="window.hacked=1">' } })
    expect(wrapper.html()).toContain('<em>ok</em>')
    expect(wrapper.html()).not.toContain('onerror')
  })
})

describe('theme', () => {
  it('applies dark as a class on <html> and mirrors the choice', () => {
    applyTheme('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
    applyTheme('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(readStoredTheme()).toBe('light')
  })

  it('falls back to system for anything unknown', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'neon')
    expect(readStoredTheme()).toBe('system')
  })
})
