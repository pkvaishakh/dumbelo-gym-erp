# StatusBadge

A membership's status as a small pill: a coloured dot and the word.

Five statuses, the same style wherever a member appears. You provide the status; never invent a sixth without adding it here.

- Active: `rl-status--active`, `volt-soft` with a `volt` dot.
- Expiring: `rl-status--expiring`, `attention-soft` with `attention` text. Use from seven days before the end date.
- Expired: `rl-status--expired`, `danger-soft` with `danger` text.
- Frozen: `rl-status--frozen`, `surface` with `ink-muted` text.
- Payment due: `rl-status--due`, outlined in `attention`.

Always show the word. The colour helps people scan; it never carries the meaning alone.

```html
<span class="rl-status rl-status--expiring">Expiring</span>
```

## Markup (from the design system preview)

```html
<div class="rl-root"><div class="rl-card rl-card--pad" style="display:flex;flex-wrap:wrap;gap:var(--space-2);max-width:358px;box-sizing:border-box"><span class="rl-status rl-status--active">Active</span><span class="rl-status rl-status--expiring">Expiring</span><span class="rl-status rl-status--expired">Expired</span><span class="rl-status rl-status--frozen">Frozen</span><span class="rl-status rl-status--due">Payment due</span></div></div>
```
