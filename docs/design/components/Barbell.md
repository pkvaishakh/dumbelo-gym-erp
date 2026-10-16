# Barbell

The brand's one picture: a loaded barbell end whose bar runs off the right edge.

Place it once per screen, between the logo and the heading, always `aria-hidden`. You provide nothing but the container: the shaft stretches to fill it.

- `rl-barbell--bleed` squares the shaft end so it can run off the screen; give the wrapper a negative right margin equal to the gutter.
- `rl-barbell--load` slides the plates onto the bar once, on load.
- `rl-barbell--lg` doubles the size; `rl-barbell--on-ink` sets it in `on-ink` for the desktop brand panel. For any other size set `--rl-u` (1 = 88px tall).

```html
<div class="rl-barbell rl-barbell--bleed rl-barbell--load" aria-hidden="true">
  <span class="rl-barbell__tip"></span>
  <span class="rl-plate rl-plate--sm"></span>
  <span class="rl-plate rl-plate--md"></span>
  <span class="rl-plate rl-plate--lg"></span>
  <span class="rl-plate"></span>
  <span class="rl-plate rl-plate--volt"></span>
  <span class="rl-barbell__collar"></span>
  <span class="rl-barbell__shaft"></span>
</div>
```

Keep exactly one `volt` plate, always the inner one. Do not put text on plates or use the barbell as a divider between sections.

## Markup (from the design system preview)

```html
<div class="rl-root"><div class="rl-barbell rl-barbell--load" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
```
