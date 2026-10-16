# AddMemberWide

Add Member from 768px.

A task keeps to one column at every width: the form is centred at 560px, with the top bar and the action bar's contents aligned to it. Fields do not spread into two columns.

## Markup (from the design system preview)

```html
<div class="rl-app rl-app--task rl-root" data-flow="add" data-step-now="2" data-static>
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-task-back aria-label="Back"><span data-back-icon="close" hidden><Icon class="rl-icon"/></span><span data-back-icon="back"><Icon class="rl-icon"/></span></button>
  <h1 class="rl-topbar__title">Add Member</h1>
  <p class="rl-topbar__aside" data-step-text>Step 2 of 3</p>
</div></header>
<main class="rl-app__main">
<div class="rl-steps"><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" data-step-bar style="--v:0.667"></span></span></div>
<form class="rl-form" data-step="1" novalidate hidden>
  <div class="rl-photopick"><span class="rl-photo rl-photo--xl" aria-hidden="true"><Icon class="rl-icon"/></span><button class="rl-button rl-button--secondary rl-button--sm" type="button"><Icon class="rl-icon rl-icon--sm"/>Add Photo</button></div>
  <div class="rl-field">
  <label class="rl-field__label" for="am-name">Full name</label>
  <div class="rl-field__control"><input class="rl-field__input" id="am-name" name="am-name" type="text" autocomplete="name" autocapitalize="words" enterkeyhint="next" placeholder="As on their ID" value="Nikhil Jain"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter the member’s full name</span></p>
</div>
  <div class="rl-field">
  <label class="rl-field__label" for="am-mobile">Mobile number</label>
  <div class="rl-field__control"><span class="rl-field__prefix">+91</span><input class="rl-field__input" id="am-mobile" name="am-mobile" type="tel" inputmode="numeric" autocomplete="tel-national" enterkeyhint="next" placeholder="10-digit number" value="90000 12291"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter a 10-digit mobile number</span></p>
</div>
  <div class="rl-field">
  <label class="rl-field__label" for="am-email">Email <span class="rl-optional">(optional)</span></label>
  <div class="rl-field__control"><input class="rl-field__input" id="am-email" name="am-email" type="email" inputmode="email" autocomplete="email" autocapitalize="none" enterkeyhint="next" placeholder="name@example.com" value="nikhil.jain@example.com"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span></span></p>
</div>
  <div class="rl-field">
  <label class="rl-field__label" for="am-dob">Date of birth <span class="rl-optional">(optional)</span></label>
  <div class="rl-field__control"><input class="rl-field__input" id="am-dob" name="am-dob" type="date" value="1996-03-14"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span></span></p>
</div>
  <fieldset class="rl-fieldset"><legend>Gender <span class="rl-optional">(optional)</span></legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="am-gender" value="Female"><span>Female</span></label><label class="rl-chipopt"><input type="radio" name="am-gender" value="Male" checked><span>Male</span></label><label class="rl-chipopt"><input type="radio" name="am-gender" value="Other"><span>Other</span></label></div></fieldset>
  <fieldset class="rl-fieldset"><legend>Goal <span class="rl-optional">(optional)</span></legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="am-goal" value="Fat Loss"><span>Fat Loss</span></label><label class="rl-chipopt"><input type="radio" name="am-goal" value="Muscle Gain" checked><span>Muscle Gain</span></label><label class="rl-chipopt"><input type="radio" name="am-goal" value="General Fitness"><span>General Fitness</span></label><label class="rl-chipopt"><input type="radio" name="am-goal" value="Strength"><span>Strength</span></label></div></fieldset>
</form>
<form class="rl-form" data-step="2" novalidate>
  <fieldset class="rl-fieldset"><legend>Plan</legend><div class="rl-choices"><label class="rl-choice"><input type="radio" name="am-plan" value="1500" data-name="Monthly" data-months="1"><span class="rl-choice__box"><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Monthly</span><span class="rl-row__meta">1 month</span></span><span class="rl-choice__price">₹1,500</span></span></label><label class="rl-choice"><input type="radio" name="am-plan" value="4500" data-name="Quarterly" data-months="3" checked><span class="rl-choice__box"><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Quarterly</span><span class="rl-row__meta">3 months</span></span><span class="rl-choice__price">₹4,500</span></span></label><label class="rl-choice"><input type="radio" name="am-plan" value="9000" data-name="Premium" data-months="3"><span class="rl-choice__box"><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Premium</span><span class="rl-row__meta">3 months, with classes and a diet plan</span></span><span class="rl-choice__price">₹9,000</span></span></label><label class="rl-choice"><input type="radio" name="am-plan" value="15000" data-name="Annual" data-months="12"><span class="rl-choice__box"><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Annual</span><span class="rl-row__meta">12 months</span></span><span class="rl-choice__price">₹15,000</span></span></label></div></fieldset>
  <div class="rl-field">
  <label class="rl-field__label" for="am-start">Start date</label>
  <div class="rl-field__control"><input class="rl-field__input" id="am-start" name="am-start" type="date" value="2026-10-05"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span></span></p>
  <p class="rl-field__hint" data-ends>Ends 4 Jan 2027</p>
</div>
  <fieldset class="rl-fieldset"><legend>Add-on <span class="rl-optional">(optional)</span></legend><div class="rl-choices"><label class="rl-choice"><input type="checkbox" name="am-pt" value="6000"><span class="rl-choice__box"><span class="rl-choice__mark rl-choice__mark--box"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Personal training</span><span class="rl-row__meta">12 sessions with a trainer</span></span><span class="rl-choice__price">₹6,000</span></span></label></div></fieldset>
  <div class="rl-field" data-trainer-field hidden><label class="rl-field__label" for="am-trainer">Trainer</label><div class="rl-field__control"><select class="rl-field__input" id="am-trainer" name="am-trainer"><option>Arjun Rao</option><option>Kavya Shetty</option><option>Neeraj Pillai</option></select><Icon class="rl-icon rl-icon--sm"/></div></div>
</form>
<div class="rl-form" data-step="3" hidden>
  <section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Member</h2><button class="rl-link" type="button" style="border:0;background:none;padding:0" data-goto="1"><span>Edit</span></button></div><div class="rl-card rl-card--pad"><div class="rl-idcard__who"><span class="rl-photo rl-photo--lg" aria-hidden="true" data-r="initials" style="background:var(--surface)">NJ</span><span><span class="rl-row__title" data-r="name">Nikhil Jain</span><span class="rl-row__meta" data-r="mobile">+91 90000 12291</span></span></div><dl class="rl-facts"><dt>Goal</dt><dd data-r="goal">Muscle Gain</dd></dl></div></section>
  <section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Membership</h2><button class="rl-link" type="button" style="border:0;background:none;padding:0" data-goto="2"><span>Edit</span></button></div><div class="rl-card rl-card--pad"><dl class="rl-facts"><dt>Plan</dt><dd data-r="plan">Quarterly</dd><dt>Period</dt><dd data-r="period">5 Oct 2026 to 4 Jan 2027</dd><dt>Personal training</dt><dd data-r="pt">Not added</dd></dl><p class="rl-total"><span>Total to pay</span><span data-total>₹4,500</span></p></div></section>
</div>
</main>
<div class="rl-actionbar"><div class="rl-actionbar__in"><div class="rl-actionbar__sum" data-total-box><span>Total</span><strong data-total>₹4,500</strong></div><button class="rl-button" type="button" data-next>Continue</button></div></div>
<div class="rl-scrim"></div>
<div class="rl-sheet" id="rl-sheet-added" role="dialog" aria-modal="true" aria-labelledby="rl-sheet-added-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="rl-sheet-added-title"><span data-r="name">Nikhil Jain</span> is now a member</h2><p class="rl-confirm__text">The membership starts once the first payment is collected.</p></div>
  <div class="rl-idcard">
    <div class="rl-idcard__who"><span class="rl-photo rl-photo--lg" aria-hidden="true" data-r="initials">NJ</span><span><span class="rl-row__title" data-r="name">Nikhil Jain</span><span class="rl-row__meta">RL-2291</span><span class="rl-status rl-status--due">Payment due</span></span></div>
    <dl class="rl-facts"><dt>Plan</dt><dd data-r="plan">Quarterly</dd><dt>Valid until</dt><dd data-r="until">4 Jan 2027</dd><dt>To pay</dt><dd data-total>₹4,500</dd></dl>
  </div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-pay-now>Collect <span data-total style="margin-left:.25em">₹4,500</span></button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-pay-later>Pay Later</button></div>
</div>
</div>
```
