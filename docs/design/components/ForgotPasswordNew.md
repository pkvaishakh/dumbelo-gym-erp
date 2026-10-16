# ForgotPasswordNew

Forgot password, step 3: the new password, here with one that is too short.

One field, "New password", with the show and hide button, and "Save Password". There is no second field to confirm: the person can show what they typed.

- The only rule is length: at least 8 characters, stated in the placeholder and in the error "Use at least 8 characters".
- Use `autocomplete="new-password"` so the phone offers to save it.

## Markup (from the design system preview)

```html
<main class="rl-auth rl-root" data-auth="forgot" data-step-now="3" data-static>
  <aside class="rl-auth__brand" aria-hidden="true">
    <div class="rl-auth__brand-art"><div class="rl-barbell rl-barbell--lg rl-barbell--on-ink rl-barbell--bleed" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
    <div>
      <p class="rl-auth__brand-line"><span>Open up.</span> <span>Check in.</span> <span>Close out.</span></p>
      <p class="rl-auth__brand-note">Members, classes and payments in one app, for every role in the gym.</p>
    </div>
  </aside>
  <div class="rl-auth__app">
    <header class="rl-auth__top rl-auth__top--back"><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-auth-back aria-label="Back"><Icon class="rl-icon"/></button><a class="rl-logo" href="#" aria-label="Rackline home"><Mark/><span class="rl-logo__name">Rackline</span></a></header>
    <div class="rl-auth__art"><div class="rl-barbell rl-barbell--bleed" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
    <section class="rl-auth__body" data-step="1" hidden aria-labelledby="fp-t1">
      <h1 class="rl-display" id="fp-t1">Reset your password</h1>
      <p class="rl-lede">Enter your mobile number or email and we’ll send you a code.</p>
      <form class="rl-auth__form" data-form="find" novalidate>
<div class="rl-field">
  <label class="rl-field__label" for="fp-id">Mobile number or email</label>
  <div class="rl-field__control"><input class="rl-field__input" id="fp-id" name="fp-id" type="text" inputmode="email" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false" enterkeyhint="send" placeholder="98765 43210 or you@gym.com"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter your mobile number or email</span></p>
</div>
        <button class="rl-button rl-button--block" type="submit"><span class="rl-button__spinner" aria-hidden="true"></span><span class="rl-button__label">Send Code</span></button>
      </form>
    </section>
    <section class="rl-auth__body" data-step="2" hidden aria-labelledby="fp-t2">
      <h1 class="rl-display" id="fp-t2">Enter the code</h1>
      <p class="rl-lede">We sent a 6-digit code to <strong data-sent-to>98765 43210</strong>.</p>
      <form class="rl-auth__form" data-form="code" novalidate>
        <div>
          <div class="rl-otp"><input class="rl-otp__input" name="fp-code" type="text" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]*" maxlength="6" enterkeyhint="done" aria-label="6-digit code" value=""><span class="rl-otp__cell is-active" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span><span class="rl-otp__cell" aria-hidden="true"></span></div>
          <p class="rl-field__error" role="alert" data-code-error hidden><Icon/><span></span></p>
        </div>
        <p class="rl-auth__resend">Didn’t get it? <span data-resend-wait>Resend in 0:24</span><a class="rl-link" href="#" data-resend hidden><span>Resend code</span></a><span data-resend-note role="status" hidden>A new code is on its way.</span></p>
        <button class="rl-button rl-button--block" type="submit" data-verify><span class="rl-button__spinner" aria-hidden="true"></span><span class="rl-button__label">Verify</span></button>
      </form>
    </section>
    <section class="rl-auth__body" data-step="3" aria-labelledby="fp-t3">
      <h1 class="rl-display" id="fp-t3">Choose a new password</h1>
      <p class="rl-lede">You’ll use it the next time you sign in.</p>
      <form class="rl-auth__form" data-form="new" novalidate>
<div class="rl-field is-invalid">
  <label class="rl-field__label" for="fp-new">New password</label>
  <div class="rl-field__control"><input class="rl-field__input" id="fp-new" name="fp-new" type="password" autocomplete="new-password" autocapitalize="none" autocorrect="off" spellcheck="false" enterkeyhint="go" placeholder="At least 8 characters" value="gym2026" aria-invalid="true"><button class="rl-field__toggle" type="button" aria-label="Show password" aria-pressed="false" aria-controls="fp-new"><Icon class="rl-eye"/><Icon class="rl-eye-off"/></button></div>
  <p class="rl-field__error" role="alert"><Icon/><span>Use at least 8 characters</span></p>
</div>
        <button class="rl-button rl-button--block" type="submit"><span class="rl-button__spinner" aria-hidden="true"></span><span class="rl-button__label">Save Password</span></button>
      </form>
    </section>
    <section class="rl-auth__body" data-step="4" hidden aria-labelledby="fp-t4">
      <span class="rl-confirm__mark rl-auth__mark" aria-hidden="true"><Icon class="rl-icon"/></span>
      <h1 class="rl-display" id="fp-t4">Password changed</h1>
      <p class="rl-lede">Sign in with your new password.</p>
      <form class="rl-auth__form" onsubmit="return false"><a class="rl-button rl-button--block" href="#" data-auth-signin>Back to Sign In</a></form>
    </section>
    <footer class="rl-auth__foot"><p class="rl-auth__join">Remembered it? <a class="rl-link" href="#" data-auth-signin><span>Sign in</span></a></p></footer>
  </div>
</main>
```
