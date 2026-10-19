# LoginScreen

The sign-in screen shared by every role, at phone width; the reference for every auth screen.

One column on `ground`: logo, barbell, "Let’s get moving", "Sign in to manage your gym", the identifier and password fields, "Forgot password?", the "Sign In" button, then the footer with "Request access" and the legal links. Nothing on it names a role; the account decides where the person lands after signing in. The same markup serves every width: `rl-auth` centres the column from 600px and adds the `ink` brand panel from 1024px (see LoginScreenTablet and LoginScreenDesktop).

You provide the form's submit handler. The script in `preview.html` is a demo: it validates empty fields, shows "Signing in…" and then "Signed in", and resets. Replace the timer with the real request, keep the validation, the return-key handling and the show/hide logic.

- Keep the order and the copy. Add nothing above the heading but the logo and the barbell.
- If sign-in offers a second method (a one-time code), add one `rl-button--secondary` under "Sign In", not a row of icons.
- Keep the footer last in the column so it sits above the home indicator and clears an open keyboard.

## Markup (from the design system preview)

```html
<main class="rl-auth rl-root">
  <aside class="rl-auth__brand" aria-hidden="true">
    <div class="rl-auth__brand-art"><div class="rl-barbell rl-barbell--lg rl-barbell--on-ink rl-barbell--bleed rl-barbell--load" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
    <div>
      <p class="rl-auth__brand-line"><span>Open up.</span> <span>Check in.</span> <span>Close out.</span></p>
      <p class="rl-auth__brand-note">Members, classes and payments in one app, for every role in the gym.</p>
    </div>
  </aside>
  <div class="rl-auth__app">
    <header class="rl-auth__top"><a class="rl-logo" href="#" aria-label="Dumbelo home"><Mark/><span class="rl-logo__name">Dumbelo</span></a></header>
    <div class="rl-auth__art"><div class="rl-barbell rl-barbell--bleed rl-barbell--load" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
    <section class="rl-auth__body" aria-labelledby="rl-title">
      <h1 class="rl-display" id="rl-title">Let’s get moving</h1>
      <p class="rl-lede">Sign in to manage your gym</p>
      <form class="rl-auth__form" id="rl-signin" novalidate>
<div class="rl-field">
  <label class="rl-field__label" for="rl-id">Mobile number or email</label>
  <div class="rl-field__control">
    <input class="rl-field__input" id="rl-id" name="username" type="text" inputmode="email" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false" enterkeyhint="next" placeholder="98765 43210 or you@gym.com" required aria-describedby="rl-id-error">
  </div>
  <p class="rl-field__error" id="rl-id-error" role="alert" hidden><Icon/><span>Enter your mobile number or email</span></p>
</div>
<div class="rl-field">
  <label class="rl-field__label" for="rl-pw">Password</label>
  <div class="rl-field__control">
    <input class="rl-field__input" id="rl-pw" name="password" type="password" autocomplete="current-password" autocapitalize="none" autocorrect="off" spellcheck="false" enterkeyhint="go" placeholder="Enter your password" required aria-describedby="rl-pw-error">
    <button class="rl-field__toggle" type="button" aria-label="Show password" aria-pressed="false" aria-controls="rl-pw"><Icon class="rl-eye"/><Icon class="rl-eye-off"/></button>
  </div>
  <p class="rl-field__error" id="rl-pw-error" role="alert" hidden><Icon/><span>Enter your password</span></p>
</div>
        <div class="rl-auth__forgot"><a class="rl-link" href="#"><span>Forgot password?</span></a></div>
        <button class="rl-button rl-button--block" type="submit"><span class="rl-button__spinner" aria-hidden="true"></span><Icon class="rl-button__icon"/><span class="rl-button__label">Sign In</span></button>
      </form>
    </section>
    <footer class="rl-auth__foot">
      <p class="rl-auth__join">Don’t have an account? <a class="rl-link" href="#"><span>Request access</span></a></p>
      <nav class="rl-auth__legal" aria-label="Legal"><a class="rl-link rl-link--plain" href="#">Terms of Service</a><a class="rl-link rl-link--plain" href="#">Privacy Policy</a></nav>
    </footer>
  </div>
</main>
```
