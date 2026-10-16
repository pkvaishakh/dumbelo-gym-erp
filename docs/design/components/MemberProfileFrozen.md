# MemberProfileFrozen

A frozen membership. Check In is replaced by one line saying check-in is paused, with Unfreeze and Collect Payment. The card reads "Frozen until 20 Oct", and Attendance says there are no check-ins while frozen.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-mprofile="desk" data-member-id="RL-1611">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Member</h1>
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-sheet="mp-more" aria-haspopup="dialog" aria-label="More actions"><Icon class="rl-icon"/></button>
</div></header>
<main class="rl-app__main">
<div class="rl-identity"><span class="rl-photo rl-photo--xl" aria-hidden="true">DK</span><div class="rl-identity__text"><h2 class="rl-identity__name">Deepa Krishnan</h2><p class="rl-identity__meta" style="margin:0"><span>RL-1611</span><span class="rl-status rl-status--frozen">Frozen</span></p></div></div>
<section class="rl-section" aria-label="Actions"><div class="rl-actions"><p class="rl-statusline" style="grid-column:1 / -1;color:var(--danger)"><Icon class="rl-icon rl-icon--sm"/>Check-in is paused while the membership is frozen.</p><button class="rl-button" type="button" data-mp="unfreeze">Unfreeze</button><a class="rl-button rl-button--secondary" href="#" data-mp="collect">Collect Payment</a><div class="rl-actions__contact"><a class="rl-button rl-button--secondary rl-button--sm" href="tel:+919000011611"><Icon class="rl-icon rl-icon--sm"/>Call</a><a class="rl-button rl-button--secondary rl-button--sm" href="sms:+919000011611"><Icon class="rl-icon rl-icon--sm"/>Message</a></div></div></section>
<div class="rl-app__cols">
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Membership</h2></div><div class="rl-pass">
  <div class="rl-pass__top"><span class="rl-status rl-status--frozen">Frozen</span><span class="rl-pass__plan">Quarterly Plan</span><a class="rl-pass__link" href="#" data-mp="renew">Manage<Icon class="rl-icon rl-icon--xs"/></a></div>
  <p class="rl-figure">Frozen <small>until 20 Oct</small></p>
  <span class="rl-bar" role="img" aria-label="35% of the plan used"><span class="rl-bar__fill" style="--v:0.352"></span></span>
  <div class="rl-pass__dates"><span>3 Sep 2026</span><span>Expires 2 Dec 2026</span></div>
  
</div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Attendance</h2><a class="rl-link" href="#" data-mp="attendance"><span>View all</span></a></div><div class="rl-card rl-card--pad"><p class="rl-row__title">No check-ins while frozen</p><p class="rl-row__meta">Last check-in on 12 Sep</p></div></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Payments</h2></div><div class="rl-card"><div style="padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--line)"><p class="rl-statusline"><span class="rl-sheet__check" style="width:24px;height:24px"><Icon class="rl-icon rl-icon--xs"/></span>No balance due</p></div><ul class="rl-activity"><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__title">Quarterly Plan, 3 months</p><p class="rl-row__meta">3 Sep 2026, Card</p></div><span class="rl-activity__amount">₹4,500</span></div></li></ul></div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Details</h2></div><div class="rl-card rl-card--pad"><dl class="rl-facts"><dt>Phone</dt><dd>+91 90000 11611</dd><dt>Email</dt><dd>deepa.krishnan@mail.example</dd><dt>Member since</dt><dd>20 Aug 2025</dd><dt>Trainer</dt><dd>None assigned</dd><dt>Goal</dt><dd>General fitness</dd></dl></div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Notes</h2><a class="rl-link" href="#"><span>Add note</span></a></div><div class="rl-card rl-card--pad"><p class="rl-row__meta" style="margin:0">No notes yet.</p></div></section></div>
</div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#" data-back><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Members</a><button class="rl-fab" type="button" data-sheet="mp-create" aria-haspopup="dialog" aria-expanded="false" aria-label="Create"><Icon class="rl-icon"/></button><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Attendance</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>
<div class="rl-sheet" id="mp-more" role="dialog" aria-modal="true" aria-labelledby="mp-more-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="mp-more-title">Member actions</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Edit Details</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Freeze Membership</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Send Renewal Reminder</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Note</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<div class="rl-sheet" id="mp-create" role="dialog" aria-modal="true" aria-labelledby="mp-create-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="mp-create-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Check In</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Member</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Collect Payment</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Subscription</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
</div>
```
