# Button

The action button: 56px tall, `radius-md`, `ink` with `on-ink` text.

One primary button per screen, full width on phones (`rl-button--block`). You provide the label and, for a submit button, the spinner and check elements shown below.

- `rl-button` is the primary action.
- `rl-button--secondary` is a `surface` fill with a `field-line` edge, for the alternative action.
- `is-loading` shows the spinner; also set `aria-busy="true"` and change the label ("Signing in…").
- `is-success` turns the button `volt` with `ink` text and pops the check in ("Signed in"). It is the only place a button is `volt`.
- `disabled` greys it to `surface` and `ink-muted`.

```html
<button class="rl-button rl-button--block" type="submit">
  <span class="rl-button__spinner" aria-hidden="true"></span>
  <svg class="rl-button__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>
  <span class="rl-button__label">Sign In</span>
</button>
```

Text links are `rl-link`: `<a class="rl-link" href="…"><span>Forgot password?</span></a>` draws the `volt` highlighter under the words and keeps a 44px tap height. Use `rl-link rl-link--plain` for legal links.

Do not put two primary buttons on a screen, shrink a button below 56px, or add an arrow to the label.

## Markup (from the design system preview)

```html
<div class="rl-root col">
  <button class="rl-button rl-button--block" type="button">Sign In</button>
  <div class="row" style="flex-wrap:nowrap">
    <button class="rl-button is-loading" type="button" aria-busy="true" style="flex:1"><span class="rl-button__spinner" aria-hidden="true"></span>Signing in…</button>
    <button class="rl-button is-success" type="button" style="flex:1"><Icon class="rl-button__icon"/> Signed in</button>
  </div>
  <div class="row" style="flex-wrap:nowrap">
    <button class="rl-button rl-button--secondary" type="button" style="flex:1">Use a code</button>
    <button class="rl-button" type="button" disabled style="flex:1">Sign In</button>
  </div>
</div>
```
