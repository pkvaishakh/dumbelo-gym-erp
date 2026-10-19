# EditStaff

Edit Trainer: the Add Trainer task with a person already filled in.

Opened from Edit Details on a Staff Profile. The title reads "Edit Trainer" or "Edit Receptionist" and the button "Save Changes". The line about the invite is gone. Saving shows "Changes saved" with the person's card, then returns to the profile with the new values.

- Same fields, same order and same validation as AddTrainer and AddReceptionist.
- The role cannot be changed here. A trainer who becomes a receptionist is a new account.

## Markup (from the design system preview)

```html
<div class="rl-app rl-app--task rl-root" data-ascreen="addstaff" data-role="trainer" data-static>
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-task-back aria-label="Close"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title"><span data-mode-word>Edit</span> <span data-role-word>Trainer</span></h1>
</div></header>
<main class="rl-app__main">
<form class="rl-form" novalidate>
  <div class="rl-field">
  <label class="rl-field__label" for="as-name">Full name</label>
  <div class="rl-field__control"><input class="rl-field__input" id="as-name" name="as-name" type="text" autocomplete="off" autocapitalize="words" enterkeyhint="next" placeholder="As on their ID" value="Arjun Rao"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter their full name</span></p>
</div>
  <div class="rl-field">
  <label class="rl-field__label" for="as-mobile">Mobile number</label>
  <div class="rl-field__control"><span class="rl-field__prefix">+91</span><input class="rl-field__input" id="as-mobile" name="as-mobile" type="tel" inputmode="numeric" autocomplete="off" enterkeyhint="next" placeholder="98765 43210" value="90000 30001"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter a 10-digit mobile number</span></p>
</div>
  <div class="rl-field">
  <label class="rl-field__label" for="as-email">Email <span class="rl-optional">(optional)</span></label>
  <div class="rl-field__control"><input class="rl-field__input" id="as-email" name="as-email" type="email" inputmode="email" autocomplete="off" autocapitalize="none" enterkeyhint="done" placeholder="name@example.com" value="arjun.rao@dumbelo.example"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span></span></p>
</div>
  <fieldset class="rl-fieldset"><legend>Branch</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="as-branch" value="Indiranagar" data-label="Indiranagar" checked><span>Indiranagar</span></label><label class="rl-chipopt"><input type="radio" name="as-branch" value="Koramangala" data-label="Koramangala"><span>Koramangala</span></label><label class="rl-chipopt"><input type="radio" name="as-branch" value="HSR Layout" data-label="HSR Layout"><span>HSR Layout</span></label><label class="rl-chipopt"><input type="radio" name="as-branch" value="Whitefield" data-label="Whitefield"><span>Whitefield</span></label></div></fieldset>
  <fieldset class="rl-fieldset" data-for-role="trainer"><legend>Specialities <span class="rl-optional">(optional)</span></legend><div class="rl-chips"><label class="rl-chipopt"><input type="checkbox" name="as-spec" value="Strength" checked><span>Strength</span></label><label class="rl-chipopt"><input type="checkbox" name="as-spec" value="Weight loss"><span>Weight loss</span></label><label class="rl-chipopt"><input type="checkbox" name="as-spec" value="Yoga"><span>Yoga</span></label><label class="rl-chipopt"><input type="checkbox" name="as-spec" value="HIIT" checked><span>HIIT</span></label><label class="rl-chipopt"><input type="checkbox" name="as-spec" value="Cardio"><span>Cardio</span></label><label class="rl-chipopt"><input type="checkbox" name="as-spec" value="Mobility"><span>Mobility</span></label></div></fieldset>
  <fieldset class="rl-fieldset" data-for-role="receptionist" hidden><legend>Shift</legend><div class="rl-choices"><label class="rl-choice"><input type="radio" name="as-shift" value="Morning" checked><span class="rl-choice__box"><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Morning</span><span class="rl-row__meta">6 AM to 2 PM</span></span></span></label><label class="rl-choice"><input type="radio" name="as-shift" value="Evening"><span class="rl-choice__box"><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Evening</span><span class="rl-row__meta">2 PM to 10 PM</span></span></span></label></div></fieldset>
  <div class="rl-field">
  <label class="rl-field__label" for="as-start">Start date</label>
  <div class="rl-field__control"><input class="rl-field__input" id="as-start" name="as-start" type="date" value="2024-01-12"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span></span></p>
</div>
  <p class="rl-field__hint" data-invite-note style="margin:0" hidden>We’ll text them an invite. Their account starts working once they set a password.</p>
</form>
</main>
<div class="rl-actionbar"><div class="rl-actionbar__in"><button class="rl-button" type="button" data-save-staff><span data-save-label hidden>Add <span data-role-word>Trainer</span></span><span data-save-edit>Save Changes</span></button></div></div>
<div class="rl-scrim"></div>
<div class="rl-sheet" id="as-done" data-modal role="dialog" aria-modal="true" aria-labelledby="as-done-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="as-done-title" data-r="title">Changes saved</h2><p class="rl-confirm__text" data-r="text" hidden>We’ve texted an invite to <span data-r="mobile">+91 98450 12345</span>. They can sign in once they set a password.</p></div>
  <div class="rl-idcard">
    <div class="rl-idcard__who"><span class="rl-photo rl-photo--lg" aria-hidden="true" data-r="initials">AR</span><span><span class="rl-row__title" data-r="name">Arjun Rao</span><span class="rl-row__meta" data-r="meta">Trainer • Indiranagar</span><span class="rl-status rl-status--active" data-r="status">On duty</span></span></div>
    <dl class="rl-facts"><dt>Started</dt><dd data-r="starts">12 Jan 2024</dd></dl>
  </div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-done="close">Done</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-done="again" hidden>Add Another</button></div>
</div>
</div>
```
