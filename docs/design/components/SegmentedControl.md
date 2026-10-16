# SegmentedControl

A small set of exclusive choices: a `surface` track with the chosen option on a `ground` pill.

You provide two to four short labels and handle the change. Mark the chosen button with `aria-pressed="true"`. `rl-seg--block` stretches the control to the full width with equal buttons.

- Use for switching a view in place (Revenue or Members; 7D, 30D or 3M). For navigation use the bottom navigation.
- Labels are one word or an abbreviation. Give the group an `aria-label`.

```html
<div class="rl-seg" role="group" aria-label="Period">
  <button class="rl-seg__btn" type="button" aria-pressed="true">7D</button>
  <button class="rl-seg__btn" type="button" aria-pressed="false">30D</button>
</div>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo" style="display:grid;gap:var(--space-4);justify-items:start"><div class="rl-card rl-card--pad" style="display:grid;gap:var(--space-3);width:100%;box-sizing:border-box"><div class="rl-seg rl-seg--block" role="group" aria-label="Measure"><button class="rl-seg__btn" type="button" aria-pressed="true">Revenue</button><button class="rl-seg__btn" type="button" aria-pressed="false">Members</button></div><div class="rl-seg" role="group" aria-label="Period" style="justify-self:start"><button class="rl-seg__btn" type="button" aria-pressed="true">7D</button><button class="rl-seg__btn" type="button" aria-pressed="false">30D</button><button class="rl-seg__btn" type="button" aria-pressed="false">3M</button></div></div></div>
```
