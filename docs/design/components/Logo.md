# Logo

The Dumbelo lockup: the plate mark and the name.

Use it once, top-left of a screen. It is a link home with a 44px tap height. It carries no role label: the same lockup serves every role. Add `rl-logo--on-ink` on an `ink` ground (the tile turns `volt`, the plates `ink`). For an app icon or favicon use `assets/Logos/dumbelo-mark.svg`.

```html
<a class="rl-logo" href="/" aria-label="Dumbelo home">
  <svg class="rl-logo__mark" viewBox="0 0 40 40" aria-hidden="true">
    <rect class="rl-logo__tile" width="40" height="40" rx="12"/>
    <rect class="rl-logo__plate" x="9.5" y="15" width="5" height="10" rx="2.5"/>
    <rect class="rl-logo__plate" x="17.5" y="12" width="5" height="16" rx="2.5"/>
    <rect class="rl-logo__plate" x="25.5" y="9" width="5" height="22" rx="2.5"/>
  </svg>
  <span class="rl-logo__name">Dumbelo</span>
</a>
```

Do not redraw the plates, change their order or recolour them outside these two versions.

## Markup (from the design system preview)

```html
<div class="rl-root row"><a class="rl-logo" href="#" aria-label="Dumbelo home"><Mark/><span class="rl-logo__name">Dumbelo</span></a><span style="display:inline-flex;padding:var(--space-2) var(--space-4);border-radius:var(--radius-md);background:var(--ink)"><a class="rl-logo rl-logo--on-ink" href="#" aria-label="Dumbelo home"><Mark/><span class="rl-logo__name">Dumbelo</span></a></span></div>
```
