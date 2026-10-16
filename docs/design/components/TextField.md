# TextField

A labelled text input, 56px tall, with an optional show/hide button and an error line.

You provide the label text, the input's `id`, `name`, `type`, `autocomplete`, `inputmode` and `enterkeyhint`, an example as placeholder, and the error message. Link the error with `aria-describedby`.

- Resting: `surface` fill, 1px `field-line` edge. Focused: `ground` fill, 2px `ink` edge and the `volt` halo.
- Invalid: add `is-invalid` to `rl-field`, set `aria-invalid="true"` on the input and remove `hidden` from the error line. Add `is-nudged` to shake it once.
- Password: add the `rl-field__toggle` button. On tap, switch the input between `type="password"` and `type="text"`, and flip `aria-pressed` and `aria-label` ("Show password" / "Hide password"). Keep focus in the input.

```html
<div class="rl-field">
  <label class="rl-field__label" for="pw">Password</label>
  <div class="rl-field__control">
    <input class="rl-field__input" id="pw" name="password" type="password"
      autocomplete="current-password" autocapitalize="none" autocorrect="off" spellcheck="false"
      enterkeyhint="go" placeholder="Enter your password" aria-describedby="pw-error">
    <button class="rl-field__toggle" type="button" aria-label="Show password" aria-pressed="false" aria-controls="pw">
      <!-- eye and eye-off SVGs: see preview.html -->
    </button>
  </div>
  <p class="rl-field__error" id="pw-error" role="alert" hidden><!-- alert SVG --><span>Enter your password</span></p>
</div>
```

On app and task screens:

- The control is `ground` instead of `surface`, automatically, inside `rl-app`.
- A fixed prefix such as "+91" goes in `rl-field__prefix` before the input.
- A skippable field adds `<span class="rl-optional">(optional)</span>` after its label.
- A line of help or a computed result ("Ends 4 Jan 2027") goes under the field in `rl-field__hint`.
- Dates use `type="date"`; a long list uses a `select` with the same class and a chevron icon after it.

Never drop the label for a placeholder, set input text below 16px, or show an error in colour alone.

## Markup (from the design system preview)

```html
<form class="rl-root col" onsubmit="return false">
<div class="rl-field">
  <label class="rl-field__label" for="tf-id">Mobile number or email</label>
  <div class="rl-field__control">
    <input class="rl-field__input" id="tf-id" name="username" type="text" inputmode="email" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false" enterkeyhint="next" placeholder="98765 43210 or you@gym.com" aria-describedby="tf-id-error">
  </div>
  <p class="rl-field__error" id="tf-id-error" role="alert" hidden><Icon/><span></span></p>
</div>
<div class="rl-field">
  <label class="rl-field__label" for="tf-pw">Password</label>
  <div class="rl-field__control">
    <input class="rl-field__input" id="tf-pw" name="password" type="password" autocomplete="current-password" autocapitalize="none" autocorrect="off" spellcheck="false" enterkeyhint="go" placeholder="Enter your password" aria-describedby="tf-pw-error" value="trainer-2026">
    <button class="rl-field__toggle" type="button" aria-label="Show password" aria-pressed="false" aria-controls="tf-pw"><Icon class="rl-eye"/><Icon class="rl-eye-off"/></button>
  </div>
  <p class="rl-field__error" id="tf-pw-error" role="alert" hidden><Icon/><span></span></p>
</div>
<div class="rl-field is-invalid">
  <label class="rl-field__label" for="tf-err">Password</label>
  <div class="rl-field__control">
    <input class="rl-field__input" id="tf-err" name="password2" type="password" autocomplete="current-password" autocapitalize="none" autocorrect="off" spellcheck="false" enterkeyhint="go" placeholder="Enter your password" aria-describedby="tf-err-error" aria-invalid="true">
    <button class="rl-field__toggle" type="button" aria-label="Show password" aria-pressed="false" aria-controls="tf-err"><Icon class="rl-eye"/><Icon class="rl-eye-off"/></button>
  </div>
  <p class="rl-field__error" id="tf-err-error" role="alert"><Icon/><span>Enter your password</span></p>
</div>
</form>
```
