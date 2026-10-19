# EditAccountSaved

The sheet that confirms saved account details.

A tick, "Details saved", one line, and Done. Done returns to Account Details, which shows the new values.

## Markup (from the design system preview)

```html
<div class="rl-app rl-app--task rl-root" data-acscreen="edit">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-task-back aria-label="Close"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Edit Details</h1>
</div></header>
<main class="rl-app__main"><form class="rl-form" novalidate onsubmit="return false">
<div class="rl-field">
  <label class="rl-field__label" for="ac-name">Full name</label>
  <div class="rl-field__control"><input class="rl-field__input" id="ac-name" name="ac-name" type="text" autocomplete="name" autocapitalize="words" enterkeyhint="next" value="Meera Nair"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter your full name</span></p>
</div>
<div class="rl-field">
  <label class="rl-field__label" for="ac-mobile">Mobile number</label>
  <div class="rl-field__control"><span class="rl-field__prefix">+91</span><input class="rl-field__input" id="ac-mobile" name="ac-mobile" type="tel" inputmode="numeric" autocomplete="tel-national" enterkeyhint="next" value="98860 12001"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter a 10-digit mobile number</span></p>
  <p class="rl-field__hint">You sign in with this number.</p>
</div>
<div class="rl-field">
  <label class="rl-field__label" for="ac-email">Email</label>
  <div class="rl-field__control"><input class="rl-field__input" id="ac-email" name="ac-email" type="email" inputmode="email" autocomplete="email" autocapitalize="none" enterkeyhint="done" value="meera.nair@dumbelo.example"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter an email address, like name@example.com</span></p>
  <p class="rl-field__hint">Receipts and reports are sent here.</p>
</div>
</form></main>
<div class="rl-actionbar"><div class="rl-actionbar__in"><button class="rl-button" type="button" data-save-account>Save Changes</button></div></div>
<div class="rl-scrim is-open"></div>
<div class="rl-sheet is-open" id="ac-saved" data-modal role="dialog" aria-modal="true" aria-labelledby="ac-saved-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="ac-saved-title">Details saved</h2><p class="rl-confirm__text">Your account details are up to date.</p></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-done>Done</button></div>
</div>
</div>
```
