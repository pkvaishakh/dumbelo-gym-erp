# ChangePassword

Change Password, from Account Details.

A task screen with two fields: Current password and New password, each with the show and hide button. A hint under the new password says what happens to other devices. The action bar's button is "Save Password", and a sheet confirms "Password changed".

- No second field to confirm the new password: the person can show what they typed.
- The only rules are at least 8 characters and different from the current one.
- Related state: ChangePasswordErrors.

## Markup (from the design system preview)

```html
<div class="rl-app rl-app--task rl-root" data-acscreen="password">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-task-back aria-label="Close"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Change Password</h1>
</div></header>
<main class="rl-app__main"><form class="rl-form" novalidate onsubmit="return false">
<div class="rl-field">
  <label class="rl-field__label" for="pw-current">Current password</label>
  <div class="rl-field__control"><input class="rl-field__input" id="pw-current" name="pw-current" type="password" autocomplete="current-password" autocapitalize="none" autocorrect="off" spellcheck="false" enterkeyhint="next"><button class="rl-field__toggle" type="button" aria-label="Show password" aria-pressed="false" aria-controls="pw-current"><Icon class="rl-eye"/><Icon class="rl-eye-off"/></button></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter your current password</span></p>
</div>
<div class="rl-field">
  <label class="rl-field__label" for="pw-new">New password</label>
  <div class="rl-field__control"><input class="rl-field__input" id="pw-new" name="pw-new" type="password" autocomplete="new-password" autocapitalize="none" autocorrect="off" spellcheck="false" enterkeyhint="done" placeholder="At least 8 characters"><button class="rl-field__toggle" type="button" aria-label="Show password" aria-pressed="false" aria-controls="pw-new"><Icon class="rl-eye"/><Icon class="rl-eye-off"/></button></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Use at least 8 characters</span></p>
  <p class="rl-field__hint">You will stay signed in on this phone. Other devices are signed out.</p>
</div>
</form></main>
<div class="rl-actionbar"><div class="rl-actionbar__in"><button class="rl-button" type="button" data-save-password>Save Password</button></div></div>
<div class="rl-scrim"></div>
<div class="rl-sheet" id="pw-saved" data-modal role="dialog" aria-modal="true" aria-labelledby="pw-saved-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="pw-saved-title">Password changed</h2><p class="rl-confirm__text">Use the new password the next time you sign in.</p></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-done>Done</button></div>
</div>
</div>
```
