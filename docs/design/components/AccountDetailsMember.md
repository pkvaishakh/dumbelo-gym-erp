# AccountDetailsMember

Account Details for a member.

In place of Role and access, a Membership section: member ID, home branch, member since. Notifications are about their own training: workout reminders, session reminders, membership ending, offers and events (off until they turn it on). The member app's tabs stay, with More current.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-acscreen="details">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Account Details</h1>
</div></header>
<main class="rl-app__main">
<div class="rl-identity"><span class="rl-photo rl-photo--xl" aria-hidden="true" data-f="initials">RK</span><div class="rl-identity__text"><h2 class="rl-identity__name" data-f="name">Rahul Kumar</h2><p class="rl-identity__meta" style="margin:0"><span>Member</span><span>•</span><span>RL-2041</span></p></div></div>
<div class="rl-app__cols">
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Personal details</h2><button class="rl-link" type="button" data-account-edit><span>Edit</span></button></div><dl class="rl-card rl-details"><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Full name</dt><dd data-f="name">Rahul Kumar</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Mobile number</dt><dd data-f="mobile">+91 90000 12041</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Email</dt><dd data-f="email">rahul.kumar@mail.example</dd></div></dl></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Membership</h2></div><dl class="rl-card rl-details"><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Member ID</dt><dd>RL-2041</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Home branch</dt><dd>Indiranagar</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Member since</dt><dd>29 Jul 2026</dd></div></dl></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Sign-in and security</h2></div><ul class="rl-card rl-remind"><li><button class="rl-remind__row" type="button" data-account-password><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-remind__text"><span class="rl-row__title">Change Password</span><span class="rl-row__meta">Last changed 29 Jul 2026</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></button></li></ul></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Notifications</h2></div><div class="rl-card"><label class="rl-setting"><span class="rl-setting__text"><span class="rl-row__title">Workout reminders</span><span class="rl-row__meta">At 7:00 AM on training days</span></span><span class="rl-switch"><input type="checkbox" role="switch" name="n-wo" checked><span></span></span></label><label class="rl-setting"><span class="rl-setting__text"><span class="rl-row__title">Session reminders</span><span class="rl-row__meta">An hour before a booked session</span></span><span class="rl-switch"><input type="checkbox" role="switch" name="n-ses" checked><span></span></span></label><label class="rl-setting"><span class="rl-setting__text"><span class="rl-row__title">Membership ending</span><span class="rl-row__meta">7 days and 1 day before it ends</span></span><span class="rl-switch"><input type="checkbox" role="switch" name="n-end" checked><span></span></span></label><label class="rl-setting"><span class="rl-setting__text"><span class="rl-row__title">Offers and events</span><span class="rl-row__meta">News from Rackline Indiranagar</span></span><span class="rl-switch"><input type="checkbox" role="switch" name="n-off"><span></span></span></label></div></section>
<section class="rl-section"><button class="rl-button rl-button--secondary rl-button--block" type="button" data-sign-out><Icon class="rl-icon rl-icon--sm"/>Sign Out</button><p class="rl-row__meta" style="margin-top:var(--space-3);text-align:center">Rackline 1.0</p></section>
</div>
</div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Workout</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Diet</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Progress</a><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>

</div>
```
