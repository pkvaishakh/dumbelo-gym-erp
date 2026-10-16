# CodeField

A one-time code as six cells that fill as it is typed.

Use for a code sent by text or email. One real input sits invisibly over six cells; the cells show the digits and the next empty one takes the focus ring. You provide the input's `name` and read its value. It needs the small script in the ForgotPassword preview to mirror the value into the cells.

- Cells are 64px tall, `surface` with a `field-line` edge, digits in the `metric` size.
- Give the input `inputmode="numeric"`, `autocomplete="one-time-code"` and `maxlength="6"`.
- An error puts a `danger` edge on all six cells, with the message under them.

```html
<div class="rl-otp">
  <input class="rl-otp__input" name="code" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" aria-label="6-digit code">
  <span class="rl-otp__cell is-active" aria-hidden="true"></span>
  <!-- five more cells -->
</div>
```

## Markup (from the design system preview)

```html
<div class="rl-root col"><div class="rl-otp"><input class="rl-otp__input" type="text" inputmode="numeric" maxlength="6" aria-label="6-digit code" value="482"><span class="rl-otp__cell" aria-hidden="true">4</span><span class="rl-otp__cell" aria-hidden="true">8</span><span class="rl-otp__cell" aria-hidden="true">2</span><span class="rl-otp__cell is-active" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span></div><div><div class="rl-otp is-invalid"><input class="rl-otp__input" type="text" inputmode="numeric" maxlength="6" aria-label="6-digit code" value=""><span class="rl-otp__cell is-active" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span></div><p class="rl-field__error" role="alert"><Icon/><span>That code is not right. Check it and try again.</span></p></div></div>
```
