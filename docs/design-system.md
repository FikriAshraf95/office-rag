> **Copied from Office Suite v2** (`office-suite-v2/docs/design-system.md`, v1.3) on 2026-11-19 for the RAG frontend ([SPEC-07](specs/SPEC-07-frontend.md)). Tokens are unchanged, so `tokens.css` copied from Office Suite stays valid. Links to SPEC-21, SPEC-23, SPEC-00 §8 and D023 point at the **Office Suite** repo. Board, Gantt, calendar, kanban and ADO rules do not apply here; the item-panel width and responsive rules are reused for the chat SourcePanel.

# Design System — Office Suite

> **Status:** v1.3 (2026-11-04, UI refresh: soft elevation, larger radii, soft-edged inputs, soft status pills) · v1.2 (2026-10-31, Poppins replaces Instrument Sans) · v1.1 (2026-10-31, UI/UX audit: neutral grey, layout and responsive rules) · v1 (2026-10-28) · **Consumed by:** [SPEC-21 §7](specs/SPEC-21-frontend.md#7-design-system-integration) and every UI milestone
> **Live system (Claude Design):** https://claude.ai/artifact/8ZqRXeTkqcJn2DwxJ5gPqe — the brand book, component previews and cover. Screens are designed in Claude Design from that system.
> **One source rule:** this file, the artifact's `tokens.json` and `frontend/src/styles/tokens.css` must hold the same values. Change all three in the same change. The token tables below are generated from the artifact's `tokens.json`.

## 1. Principles

- **Calm frame, colourful data.** The UI chrome is neutral. Colour is reserved for user data, through the label palette, plus the deep ocean brand (`#004d70`) for primary actions, selection and links. Teal `#45b3cb` and sky `#38bdf8` are fill-only accents in the light theme, and in the dark theme they become the brand and link colours. The app canvas is a soft grey (`#f6f8f9`) with the page on a white sheet.
- **Dense but legible.** The default board row is 40px, with a compact 32px option. Grid text is 13px, UI text is 14px, and numerals are tabular.
- **Soft elevation.** Hairline borders separate content inside a surface. Cards, the page sheet and secondary buttons rest on a light `shadow-sm`; things that float use `shadow-md` or `shadow-lg`.
- **Controls read by shape.** Inputs and selects are flat white fields with a soft edge; secondary buttons are raised with `shadow-sm`. The two must never look alike.
- **Accessible in both themes.** Every text pair meets WCAG AA. Borders, focus rings and the brand colour meet 3:1. Status is never shown by colour alone.
- **Copy:** sentence case, buttons that name their action, errors that say how to fix the problem, no emoji. The full voice rules are in the artifact README.

## 2. Colour tokens

CSS variables are named `--<token>`. Theme switching uses `class="dark"` on `<html>` in the app, or `data-theme` in the artifact.

| Token | Light | Dark | Usage |
|---|---|---|---|
| `surface-page` | `#f6f8f9` | `#0e1418` | App canvas behind the sidebar and the page sheet. Never put body text directly on it without `ink`. |
| `surface` | `#ffffff` | `#151c21` | Board grid, cards, item panel, dialogs. The default ground for `ink`, `ink-muted`, `ink-subtle`. |
| `surface-sunken` | `#f3f5f6` | `#1b242a` | Grid column headers, group footers, read-only fields. |
| `surface-raised` | `#ffffff` | `#212b32` | Popovers, menus, toasts (always with a shadow). |
| `surface-hover` | `#e8eef1` | `#26323a` | Hover fill for rows, menu items, sidebar entries. |
| `surface-selected` | `#dcedf3` | `#0f3446` | Selected rows, active sidebar entry, current view tab. Text on it uses `brand-ink`. |
| `border` | `#dce2e5` | `#2a363e` | Grid lines, card and panel edges, dividers. Decorative only. |
| `border-strong` | `#7a868e` | `#66747d` | Checkbox and radio outlines at rest, scrollbar thumbs; must stay 3:1 on `surface` and `surface-sunken`. |
| `border-input` | `#c9d2d7` | `#3a4852` | Soft edge of inputs, selects and textareas at rest; it darkens to `border-strong` on hover. Below 3:1 by decision, see [D023](deviations/D023-soft-input-edge-below-3-to-1.md). |
| `ink` | `#17222a` | `#e6edf1` | Primary text on `surface`, `surface-page`, `surface-sunken`, `surface-raised`. |
| `ink-muted` | `#4c5a63` | `#a6b4bd` | Secondary text: metadata, column headers, timestamps. On every surface. |
| `ink-subtle` | `#5d6a72` | `#8a99a3` | Placeholders, disabled labels, empty-cell hints. On `surface` and `surface-sunken` only. |
| `brand` | `#004d70` | `#45b3cb` | Brand colour (#004d70 light, #45b3cb dark): the one primary button per view, checked checkboxes, the org mark. Fill only with `on-brand` text. |
| `brand-hover` | `#003a55` | `#6cc6da` | Hover / pressed state of `brand` fills. |
| `on-brand` | `#ffffff` | `#04202b` | Text and icons on `brand` and `brand-hover`. |
| `brand-ink` | `#004d70` | `#38bdf8` | Links and accent text on `surface`, and any text on `surface-selected`. |
| `focus-ring` | `#0278b3` | `#38bdf8` | 2px focus outline with 2px offset on every interactive element. 3:1 on all surfaces. |
| `accent` | `#45b3cb` | `#45b3cb` | Brand teal for FILLS ONLY: chart primary series, progress fills, cover, empty-state shapes. Never text or a meaningful border on light surfaces (2.5:1 on white). |
| `accent-bright` | `#38bdf8` | `#38bdf8` | Sky highlight for FILLS ONLY: real-time change flash outline, chart second series, cover. Never text on light surfaces (2.1:1 on white). |
| `on-accent` | `#04202b` | `#04202b` | Text on `accent` and `accent-bright` fills (e.g. a value label inside a chart bar). |
| `danger` | `#b42318` | `#ff8a7a` | Destructive text and icons, overdue dates, validation errors on `surface`. |
| `danger-fill` | `#b42318` | `#e5534b` | Destructive button fill, with `on-danger` text. |
| `on-danger` | `#ffffff` | `#1d0705` | Text on `danger-fill`. |
| `danger-soft` | `#fde8e6` | `#3a1714` | Error banner / inline error background; text on it uses `danger`. |
| `warning` | `#8a5300` | `#f2b84b` | Warning text and icons on `surface` and on `warning-soft`. |
| `warning-soft` | `#fff2d9` | `#33270f` | Warning banner background (e.g. 'Editing description replaces ADO formatting'). |
| `success` | `#1d7240` | `#5fd38d` | Success text and icons on `surface` and on `success-soft`. |
| `success-soft` | `#e3f4ea` | `#143323` | Success toast / banner background. |
| `info` | `#0b62a8` | `#7ab8ff` | Info text and icons on `surface` and on `info-soft`. |
| `info-soft` | `#e4f0fb` | `#14263a` | Info banner background (e.g. 'Reconnecting…'). |
| `scrim` | `rgba(14, 20, 24, 0.48)` | `rgba(0, 0, 0, 0.6)` | Overlay behind dialogs and the mobile sidebar. |

### 2.1 Label palette

Status labels, dropdown dots, group bars, workspace marks and avatars all use these. Columns store the colour **name**, for example `"color": "green"`, never a hex value.

| Token | Light | Dark | Usage |
|---|---|---|---|
| `label-grey` | `#c4c8d0` | `#7d8590` | Neutral states: 'Not started', 'Backlog'. The default label colour. A quiet fill, so untouched rows don't shout (monday's light grey). Fill for status pills, dropdown dots, group bars. |
| `on-label-grey` | `#17222a` | `#0d0f12` | Text on `label-grey` fills. |
| `label-red` | `#c4302b` | `#e5534b` | Blocking states: 'Stuck', 'Critical'. Never the only signal: the label text always shows. Fill for status pills, dropdown dots, group bars. |
| `on-label-red` | `#ffffff` | `#1d0705` | Text on `label-red` fills. |
| `label-orange` | `#c2470c` | `#f0883e` | Attention states: 'High', 'Waiting on review'. Fill for status pills, dropdown dots, group bars. |
| `on-label-orange` | `#ffffff` | `#1f0e02` | Text on `label-orange` fills. |
| `label-amber` | `#f0b429` | `#d9a21b` | In-progress states: 'Working on it', 'Medium'. Dark text, never white. Fill for status pills, dropdown dots, group bars. |
| `on-label-amber` | `#2e2100` | `#231900` | Text on `label-amber` fills. |
| `label-green` | `#1f8048` | `#3fb26d` | Done states: 'Done', 'Approved', 'Low'. Usually the `isDone` label. Fill for status pills, dropdown dots, group bars. |
| `on-label-green` | `#ffffff` | `#05170c` | Text on `label-green` fills. |
| `label-teal` | `#0f7470` | `#2fb3ad` | Secondary progress states; also the default group colour. Fill for status pills, dropdown dots, group bars. |
| `on-label-teal` | `#ffffff` | `#031716` | Text on `label-teal` fills. |
| `label-cyan` | `#0b6a8c` | `#36a9d2` | Informational states: 'In QA', 'Scheduled'. Fill for status pills, dropdown dots, group bars. |
| `on-label-cyan` | `#ffffff` | `#02141b` | Text on `label-cyan` fills. |
| `label-blue` | `#2c62cf` | `#5b8ef0` | Active work: 'Active', 'In progress' (ADO-style). Fill for status pills, dropdown dots, group bars. |
| `on-label-blue` | `#ffffff` | `#050e20` | Text on `label-blue` fills. |
| `label-indigo` | `#4a4fc1` | `#8287f0` | Planning states: 'Planned', 'Ready'. Fill for status pills, dropdown dots, group bars. |
| `on-label-indigo` | `#ffffff` | `#0b0c26` | Text on `label-indigo` fills. |
| `label-purple` | `#7a3aa8` | `#b07ce0` | Review / design states. Fill for status pills, dropdown dots, group bars. |
| `on-label-purple` | `#ffffff` | `#1a0a28` | Text on `label-purple` fills. |
| `label-pink` | `#be2a6d` | `#ec6aa4` | Marketing / people-facing categories. Fill for status pills, dropdown dots, group bars. |
| `on-label-pink` | `#ffffff` | `#25051a` | Text on `label-pink` fills. |
| `label-brown` | `#85583a` | `#c08d68` | Archive-like or external states: 'On hold', 'Vendor'. Fill for status pills, dropdown dots, group bars. |
| `on-label-brown` | `#ffffff` | `#1d1006` | Text on `label-brown` fills. |
| `label-grey-soft` | `#eceff1` | `#2a333a` | Soft status pill tint. |
| `on-label-grey-soft` | `#4c5a63` | `#b9c4cc` | Text and dot on `label-grey-soft`. |
| `label-red-soft` | `#fbe6e4` | `#3f1b19` | Soft status pill tint. |
| `on-label-red-soft` | `#a11f1a` | `#ffa79c` | Text and dot on `label-red-soft`. |
| `label-orange-soft` | `#fcebdf` | `#3e2312` | Soft status pill tint. |
| `on-label-orange-soft` | `#9a3a08` | `#ffb27f` | Text and dot on `label-orange-soft`. |
| `label-amber-soft` | `#fdf1d3` | `#3a2c0c` | Soft status pill tint. |
| `on-label-amber-soft` | `#6f4b00` | `#f2c55c` | Text and dot on `label-amber-soft`. |
| `label-green-soft` | `#e0f2e7` | `#14351f` | Soft status pill tint. |
| `on-label-green-soft` | `#176038` | `#7fdca3` | Text and dot on `label-green-soft`. |
| `label-teal-soft` | `#dcf0ee` | `#0f3432` | Soft status pill tint. |
| `on-label-teal-soft` | `#0b5c58` | `#6fd8d2` | Text and dot on `label-teal-soft`. |
| `label-cyan-soft` | `#dcf0f6` | `#0f3240` | Soft status pill tint. |
| `on-label-cyan-soft` | `#0a5873` | `#7fd0ee` | Text and dot on `label-cyan-soft`. |
| `label-blue-soft` | `#e4ecfb` | `#182a4c` | Soft status pill tint. |
| `on-label-blue-soft` | `#2350ad` | `#a3c1ff` | Text and dot on `label-blue-soft`. |
| `label-indigo-soft` | `#e8e9fa` | `#22234c` | Soft status pill tint. |
| `on-label-indigo-soft` | `#3e42a8` | `#b4b8ff` | Text and dot on `label-indigo-soft`. |
| `label-purple-soft` | `#f0e6f7` | `#31204a` | Soft status pill tint. |
| `on-label-purple-soft` | `#662e8e` | `#d3aef2` | Text and dot on `label-purple-soft`. |
| `label-pink-soft` | `#fbe4ee` | `#401a30` | Soft status pill tint. |
| `on-label-pink-soft` | `#a3225c` | `#f7a3c8` | Text and dot on `label-pink-soft`. |
| `label-brown-soft` | `#f2e9e2` | `#352519` | Soft status pill tint. |
| `on-label-brown-soft` | `#6f4930` | `#dcb496` | Text and dot on `label-brown-soft`. |

## 3. Typography

- `--font-sans`: "Poppins", "Segoe UI", system-ui, sans-serif
- `--font-mono`: "JetBrains Mono", ui-monospace, Consolas, monospace
- **In the app:** self-host the fonts, because the CSP blocks font CDNs ([SPEC-23 §3](specs/SPEC-23-deployment-and-ops.md#3-nginx)). Poppins comes from `frontend/src/assets/fonts/poppins/` (WOFF2, weights 400, 500 and 600, `latin` and `latin-ext` subsets from Fontsource, SIL OFL 1.1, licence beside the files) and JetBrains Mono from `@fontsource/jetbrains-mono`.
- **Width:** Poppins sets wider than the previous Instrument Sans. Truncate long names and labels instead of letting them wrap in tables, cards and the sidebar.

| Style | Family | Size / line | Weight | Usage |
|---|---|---|---|---|
| `display` | sans | 28px / 34px | 600, tracking -0.01em | Workspace and dashboard page titles. One per page. |
| `title-lg` | sans | 22px / 28px | 600, tracking -0.005em | Board name in the board header; item name at the top of the item panel. |
| `title` | sans | 17px / 24px | 600 | Dialog and panel titles, group headers on the board. |
| `body` | sans | 14px / 20px | 400 | Default UI text: forms, menus, update threads, notifications. |
| `body-strong` | sans | 14px / 20px | 600 | Item names in lists and cards, button labels, emphasised values. |
| `cell` | sans | 13px / 18px | 400 | Board grid cells, kanban card fields, status pill labels (weight 500). |
| `caption` | sans | 12px / 16px | 500 | Metadata, column headers, timestamps, counts. Use `ink-muted`. |
| `overline` | sans | 11px / 16px | 600, tracking 0.06em | Sidebar section labels and group-footer summary labels, uppercase. |
| `mono` | mono | 12px / 16px | 500 | Azure DevOps IDs, column keys, trace IDs. Never for prose. |

**Dates** always go through `lib/format`, in the organisation timezone: `26 Oct` (day), `26 Oct 09:30` (day and time), `Mon 26` (calendar week headers), `Oct 2026` (month headers). Never `10/26`.

**Column headers** use `caption` in `ink-muted`, with the type icon right before the label (gap 6px), so the data stands forward.

## 4. Spacing

| Token | Value | Usage |
|---|---|---|
| `space-0.5` | `2px` | Inset of a status pill inside its cell; icon-to-count gap. |
| `space-1` | `4px` | Gap between avatar stack items, chip internal padding (vertical). |
| `space-1.5` | `6px` | Chip horizontal padding, gap inside compact controls. |
| `space-2` | `8px` | Cell horizontal padding, gap between inline controls. |
| `space-3` | `12px` | Button horizontal padding, card padding in kanban, menu item padding. |
| `space-4` | `16px` | Panel and dialog padding, page side gutter on narrow screens. |
| `space-5` | `20px` | Gap between form fields. |
| `space-6` | `24px` | Page gutter, gap between board groups. |
| `space-8` | `32px` | Gap between page sections; dashboard widget gap. |
| `space-12` | `48px` | Empty-state vertical padding. |

## 5. Radius

| Token | Value | Usage |
|---|---|---|
| `radius-xs` | `4px` | Chips, checkbox. |
| `radius-sm` | `6px` | Small buttons, tooltips, tags. |
| `radius-md` | `8px` | Buttons, inputs, selects, view tabs, menu items. |
| `radius-lg` | `12px` | Cards, popovers, kanban cards, dashboard widgets, toasts. |
| `radius-xl` | `16px` | Dialogs and the page sheet. |
| `radius-full` | `9999px` | Avatars, status pills, count badges, toggle switches. |

## 6. Fixed sizes

| Token | Value | Usage |
|---|---|---|
| `row-comfortable` | `40px` | Board table row height, comfortable density (default). |
| `row-compact` | `32px` | Board table row height, compact density. |
| `control-h` | `36px` | Height of buttons, inputs, selects, view tabs. |
| `control-h-sm` | `28px` | Height of toolbar buttons and in-cell controls. |
| `avatar-sm` | `24px` | Avatars in cells, cards and activity rows. |
| `avatar-md` | `32px` | Avatars in update threads and the profile menu. |
| `group-bar` | `4px` | Width of the coloured group bar on the left of board rows. |
| `sidebar-w` | `264px` | Expanded sidebar width. |
| `sidebar-rail-w` | `56px` | Collapsed sidebar (icon rail), and the default from 1024 to 1279px. |
| `page-w-reading` | `768px` | Max width of form pages (profile, settings forms). Left-aligned. |
| `control-h-touch` | `44px` | Control and tap-target height on coarse pointers (touch). |
| `item-panel-w` | `600px` | Default item panel width (resizable 480–960px). |

## 7. Shadows

| Token | Light | Dark | Usage |
|---|---|---|---|
| `shadow-sm` | `0 1px 2px rgba(20, 28, 24, 0.08)` | `0 1px 2px rgba(0, 0, 0, 0.5)` | Cards, the page sheet and secondary buttons at rest, sticky grid header when scrolled. |
| `shadow-md` | `0 4px 12px rgba(20, 28, 24, 0.12), 0 1px 3px rgba(20, 28, 24, 0.08)` | `0 4px 14px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.04)` | Popovers, menus, toasts, a dragged card. |
| `shadow-lg` | `0 12px 32px rgba(20, 28, 24, 0.18)` | `0 12px 36px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.05)` | Dialogs and the item panel drawer. |

## 8. States & motion

| State | Treatment |
|---|---|
| Hover | `surface-hover` |
| Selected | `surface-selected` with `brand-ink` text |
| Focus | 2px solid `focus-ring`, 2px offset. Never removed. Text inputs, selects and textareas draw it over their own edge (offset -1px). |
| Disabled | 50% opacity, plus a tooltip explaining why. Buttons of every variant instead turn neutral: `surface-sunken` fill, `ink-muted` text, no border or shadow, 60% opacity and a not-allowed cursor, so a disabled primary never reads as a light primary. |
| Loading | Skeletons on `surface-sunken`. No spinners in the grid. |
| Real-time change by someone else | 600ms `surface-selected` flash with a 1px `accent-bright` inner outline |
| Invalid field | `danger` border on `surface`, an error icon beside the message, and the focus ring turns `danger` too (one ring, never two) |
| Row actions | Comment, open and `⋯` icons on a row fade in on hover or focus (120ms); hidden at rest |
| Now / today | The Gantt today line and the calendar now-indicator use `brand-ink`, 2px. `danger` stays for overdue only. Today's date number sits in a 24px `brand` circle with `on-brand` text. |

**Scrollbars:** thin, without arrow buttons (`::-webkit-scrollbar` in Chromium and Safari, with `::-webkit-scrollbar-button` at `display: none` **and** zero size, or Chromium still paints the arrows; `scrollbar-width: thin` in Firefox) and auto-hiding: the thumb is transparent at rest and
shows in `border-strong` while the scroller is hovered or holds focus. Scrolling is never disabled or
hidden for real, so wheel, trackpad, touch and keyboard (arrows, Page Up/Down, Space) keep working.
A scroller that must always show its thumb adds the `scrollbar-visible` class. No new tokens.

**Motion:**
- Popovers and menus: fade plus a 4px slide, 120ms ease-out.
- Item panel: 180ms slide.
- Dragged card: lifts with `shadow-md` and a 1.5° tilt.
- State changes (status colour, group collapse, row-action fade): 150ms ease-out.
- `prefers-reduced-motion` turns slides into fades and removes the flash.

## 9. Iconography

- **Library:** Lucide (`lucide-vue-next`), outline style, 16px, stroke 2, `currentColor`. 20px only in empty states and the top bar.
- **No emoji** in product UI.
- **View icons:** Table, SquareKanban, Calendar, ChartGantt.
- **Column type icons:** Type, AlignLeft, Hash, CircleDot, Tags, Users, Calendar, SquareCheck, Link, Paperclip, GitBranch, ListOrdered (auto-number), Sigma (rollup). Restricted columns show Lock in the header.
- **Private boards** show Lock after the name.

## 10. Components (target look)

Each component has a live preview and a README in the artifact. The app implements them as Vue components on shadcn-vue, reading these tokens.

| Group | Components |
|---|---|
| Actions | Button: primary (one per view), secondary, ghost (toolbars), danger (only inside confirmations) |
| Forms | Input (label, help, error), Textarea, Select (a styled popup, never the browser's list), DatePicker and TimePicker (typed or picked, in the organisation's date format and first day of the week; times are 24-hour), PasswordInput (an Input with an eye button that shows or hides the typed text; use it for every password and secret field), Checkbox, Switch (on/off settings), RadioGroup and RadioCard (a selectable card with a title and description, for choices that need explaining), HoursSelect (a popover with typed entry, an hour grid and Use remaining, for Plan and Actual WIP) |
| Board | BoardHeader (ghost buttons for Automate, Integrate, Activity; Members as an avatar stack; the one primary button is *New item*), StatusPill (a `radius-full` pill on `label-*-soft` with `on-label-*-soft` text and a 6px dot; widths follow the label), Chip (neutral chip plus colour dot, at most 2 then `+n`), ViewTabs, BoardTable (group bar, sticky name column, typed cells, add row, summary row), KanbanCard (lanes on `surface-sunken`) |
| People | Avatar: initials on a label colour derived from the user ID; stacks of 3 then `+n`; inactive users greyed |
| Collaboration | UpdateCard (mentions use `brand-ink` on `surface-selected`), NotificationItem (unread shows bold plus a brand dot) |
| Feedback | CountBadge (unread uses `danger-fill`), Banner (semantic soft colours, an icon and an optional action), Skeleton (loading blocks and rows; keeps an sr-only label), Tooltip (the reason a control is disabled, or the name of an icon button), Toast (5 seconds, Undo for bulk actions) |
| Data | DataTable (a card around a real table: sunken header, comfortable rows, hover fill), Tabs (`underline` for page sections, `segmented` for filters and small switches) |
| Navigation | Three flush regions, no floating sheet. Sidebar: full height on `surface` with a right border; the logo row is 56px with a bottom border, level with the top bar; the current entry is `surface-selected` with `brand-ink` text and a 2px `brand` bar on its left edge. TopBar: 56px on `surface`, full width of the content column, bottom border; demo-user switcher and theme toggle on the right. Content: `main` on `surface-page`, so cards, tables and panels (`surface` + border) stand out; it fills the window on phones, where the sidebar is a drawer over a `scrim`. |

## 11. Layout and breakpoints

**Page container.** Every routed page sits in `PageContainer`, left-aligned at the `main` gutter (24px from the sidebar, 16px on phones), so the page title never moves between pages. There are two widths only: `wide` for data pages, which fills the window like board pages, and `reading` (`page-w-reading`) for form pages. Pages never centre themselves (`mx-auto`) or pick their own max width.

| Range | Sidebar | Item panel | Table | Calendar | Gantt |
|---|---|---|---|---|---|
| ≥ 1280px | 264px, collapsible to the rail | Beside the content (`item-panel-w`) | Full | Grid plus the Unscheduled panel | Name column 280px |
| 1024–1279px | Rail (`sidebar-rail-w`) | Overlay with `scrim` | Full, horizontal scroll | Unscheduled collapsed to a rail | Name column 220px |
| 768–1023px | Drawer | Overlay, 85% wide | Full; sticky name column 220px | Unscheduled collapsed to a rail | Name column 160px |
| < 768px | Drawer | Full screen, with a back button | Card list per group | Agenda list (by day) | No name column; names drawn in or beside the bars |

**Phones (< 768px):** the board header keeps the name, the Members stack and a `⋯` menu holding the other actions; view tabs scroll in one row; the toolbar keeps the primary button, a search icon and one *Filter* button. On coarse pointers, controls are `control-h-touch` tall.

**Empty space:** an empty Unscheduled panel collapses to a 40px rail with its count; an empty group hides its summary row; a workspace with fewer than 4 boards shows a *Create a board* card.

## 12. Branding

- There is **no product logo yet**, and the name is a placeholder ([SPEC-00 §8](specs/SPEC-00-overview.md#8-open-items)). The sidebar shows the organisation's uploaded logo, or its initials in a `brand` square with `radius-md`.
- Never draw an invented logo, and never use third-party marks. Microsoft and Azure DevOps are named in text only.

