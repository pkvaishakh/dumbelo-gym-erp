# MemberProfileExpired

The Member Profile for a member whose membership has expired.

The badge reads Expired, a `danger` line above the actions says check-in is blocked until renewal, and the first action is "Renew" with "Collect Payment" beside it. The membership card is `danger-soft`, counts the days since it expired, and its bar is full. This is where "View Profile" leads from a blocked check-in.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Member</h1>
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-sheet="px-more" aria-haspopup="dialog" aria-label="More actions"><Icon class="rl-icon"/></button>
</div></header>
<main class="rl-app__main">
<div class="rl-identity"><span class="rl-photo rl-photo--xl" aria-hidden="true">RM</span><div class="rl-identity__text"><h2 class="rl-identity__name">Raghav Menon</h2><p class="rl-identity__meta" style="margin:0"><span>RL-1532</span><span class="rl-status rl-status--expired">Expired</span></p></div></div>
<section class="rl-section" aria-label="Actions"><div class="rl-actions">
  <p class="rl-statusline" style="grid-column:1 / -1;color:var(--danger)"><Icon class="rl-icon rl-icon--sm"/>Check-in is blocked until this membership is renewed.</p>
  <button class="rl-button" type="button">Renew</button>
  <a class="rl-button rl-button--secondary" href="#">Collect Payment</a>
  <div class="rl-actions__contact"><a class="rl-button rl-button--secondary rl-button--sm" href="#"><Icon class="rl-icon rl-icon--sm"/>Call</a><a class="rl-button rl-button--secondary rl-button--sm" href="#"><Icon class="rl-icon rl-icon--sm"/>Message</a></div>
</div></section>
<div class="rl-app__cols">
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Membership</h2></div><div class="rl-pass rl-pass--expired">
  <div class="rl-pass__top"><span class="rl-status rl-status--expired" style="background:var(--ground)">Expired</span><span class="rl-pass__plan">Monthly Plan</span><a class="rl-pass__link" href="#">Manage<Icon class="rl-icon rl-icon--xs"/></a></div>
  <p class="rl-figure">7 <small>days since it expired</small></p>
  <span class="rl-bar" role="img" aria-label="Plan period finished"><span class="rl-bar__fill" style="--v:1.000"></span></span>
  <div class="rl-pass__dates"><span>29 Aug 2026</span><span>Expired 28 Sep 2026</span></div>
</div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Attendance</h2><a class="rl-link" href="#"><span>View all</span></a></div><div class="rl-card rl-card--pad"><p class="rl-row__title">Last check-in on 27 Sep</p><p class="rl-row__meta">11 check-ins in the last 30 days</p></div></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Details</h2></div><div class="rl-card rl-card--pad"><dl class="rl-facts"><dt>Phone</dt><dd>+91 90000 11532</dd><dt>Member since</dt><dd>29 Aug 2026</dd><dt>Trainer</dt><dd>None assigned</dd></dl></div></section></div>
</div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#" data-back><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Members</a><button class="rl-fab" type="button" data-sheet="px-create" aria-haspopup="dialog" aria-expanded="false" aria-label="Create"><Icon class="rl-icon"/></button><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Attendance</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>
<div class="rl-sheet" id="px-more" role="dialog" aria-modal="true" aria-labelledby="px-more-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="px-more-title">Member actions</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Edit Details</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Freeze Membership</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Send Renewal Reminder</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Note</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<div class="rl-sheet" id="px-create" role="dialog" aria-modal="true" aria-labelledby="px-create-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="px-create-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Check In</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Member</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Collect Payment</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Subscription</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
</div>
```
