# RequestAccessErrors

Request access after pressing the button with the form incomplete.

Each field says what to do under itself: "Enter your full name", "Enter a 10-digit mobile number", "Choose your branch". Focus moves to the first one, and each message clears as its field is filled.

## Markup (from the design system preview)

```html
<main class="rl-auth rl-root" data-auth="request" data-step-now="1" data-static>
  <aside class="rl-auth__brand" aria-hidden="true">
    <div class="rl-auth__brand-art"><div class="rl-barbell rl-barbell--lg rl-barbell--on-ink rl-barbell--bleed" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
    <div>
      <p class="rl-auth__brand-line"><span>Open up.</span> <span>Check in.</span> <span>Close out.</span></p>
      <p class="rl-auth__brand-note">Members, classes and payments in one app, for every role in the gym.</p>
    </div>
  </aside>
  <div class="rl-auth__app">
    <header class="rl-auth__top rl-auth__top--back"><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-auth-back aria-label="Back to sign in"><Icon class="rl-icon"/></button><a class="rl-logo" href="#" aria-label="Rackline home"><Mark/><span class="rl-logo__name">Rackline</span></a></header>
    <div class="rl-auth__art"><div class="rl-barbell rl-barbell--bleed" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
    <section class="rl-auth__body" data-step="1" aria-labelledby="ra-t1">
      <h1 class="rl-display" id="ra-t1">Request access</h1>
      <p class="rl-lede">Tell your gym who you are and they’ll set up your account.</p>
      <form class="rl-auth__form" data-form="request" novalidate>
<div class="rl-field is-invalid">
  <label class="rl-field__label" for="ra-name">Full name</label>
  <div class="rl-field__control"><input class="rl-field__input" id="ra-name" name="ra-name" type="text" autocomplete="name" autocapitalize="words" enterkeyhint="next" placeholder="As on your ID" aria-invalid="true"></div>
  <p class="rl-field__error" role="alert"><Icon/><span>Enter your full name</span></p>
</div>
<div class="rl-field is-invalid">
  <label class="rl-field__label" for="ra-mobile">Mobile number</label>
  <div class="rl-field__control"><span class="rl-field__prefix">+91</span><input class="rl-field__input" id="ra-mobile" name="ra-mobile" type="tel" inputmode="numeric" autocomplete="tel-national" enterkeyhint="next" placeholder="98765 43210" value="98765" aria-invalid="true"></div>
  <p class="rl-field__error" role="alert"><Icon/><span>Enter a 10-digit mobile number</span></p>
</div>
        <div class="rl-field is-invalid">
          <label class="rl-field__label" for="ra-branch">Branch</label>
          <div class="rl-field__control"><select class="rl-field__input" id="ra-branch" name="ra-branch" required aria-invalid="true"><option value="" selected>Choose your branch</option><option>Indiranagar</option><option>Koramangala</option><option>HSR Layout</option><option>Whitefield</option></select><Icon class="rl-icon rl-icon--sm"/></div>
          <p class="rl-field__error" role="alert"><Icon/><span>Choose your branch</span></p>
        </div>
        <button class="rl-button rl-button--block" type="submit"><span class="rl-button__spinner" aria-hidden="true"></span><span class="rl-button__label">Request Access</span></button>
      </form>
    </section>
    <section class="rl-auth__body" data-step="2" hidden aria-labelledby="ra-t2">
      <span class="rl-confirm__mark rl-auth__mark" aria-hidden="true"><Icon class="rl-icon"/></span>
      <h1 class="rl-display" id="ra-t2">Request sent</h1>
      <p class="rl-lede">The <strong data-ra-branch>Indiranagar</strong> team will review it and text you on <strong data-ra-mobile>+91 98765 43210</strong> when your account is ready.</p>
      <form class="rl-auth__form" onsubmit="return false"><a class="rl-button rl-button--block" href="#" data-auth-signin>Back to Sign In</a></form>
    </section>
    <footer class="rl-auth__foot"><p class="rl-auth__join">Already have an account? <a class="rl-link" href="#" data-auth-signin><span>Sign in</span></a></p>
      <nav class="rl-auth__legal" aria-label="Legal"><a class="rl-link rl-link--plain" href="#">Terms of Service</a><a class="rl-link rl-link--plain" href="#">Privacy Policy</a></nav></footer>
  </div>
</main>
```
