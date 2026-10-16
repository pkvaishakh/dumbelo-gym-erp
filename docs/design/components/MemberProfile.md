# MemberProfile

The Member Profile as the front desk and admins see it, at phone width and full scroll length.

A detail screen for one member. Top to bottom: a top bar (back, "Member", more actions), the ProfileHeader with its actions, the membership card with the personal-training pack under it, the next session, attendance, payments, details and notes. The bottom navigation stays, with Members as the current tab.

You provide the member's record and the targets. The script in `preview.html` opens the two sheets and, as a demo, swaps the Check In button for "Checked in at 8:41 AM". Replace that with the real check-in.

- The first action depends on the member's state: "Check In" when they can check in, a "Checked in at…" line once they have, "Renew" when the membership has expired.
- Payments show single payments and whether a balance is due. No revenue totals.
- Figures match the home screens: the plan dates, the days remaining, the trainer and the next session are the same ones Receptionist Home and Member Home show.
- Related: MemberProfileTrainer, MemberProfileExpired, MemberProfileActions, MemberProfileWide.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Member</h1>
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-sheet="pd-more" aria-haspopup="dialog" aria-label="More actions"><Icon class="rl-icon"/></button>
</div></header>
<main class="rl-app__main">
<div class="rl-identity"><span class="rl-photo rl-photo--xl" aria-hidden="true">RK</span><div class="rl-identity__text"><h2 class="rl-identity__name">Rahul Kumar</h2><p class="rl-identity__meta" style="margin:0"><span>RL-2041</span><span class="rl-status rl-status--active">Active</span></p></div></div>
<section class="rl-section" aria-label="Actions"><div class="rl-actions">
  <button class="rl-button" type="button" data-session="in" data-when="out">Check In</button>
  <p class="rl-statusline" data-when="in" hidden style="align-self:center"><span class="rl-sheet__check" style="width:24px;height:24px"><Icon class="rl-icon rl-icon--xs"/></span>Checked in at 8:41 AM</p>
  <a class="rl-button rl-button--secondary" href="#">Collect Payment</a>
  <div class="rl-actions__contact"><a class="rl-button rl-button--secondary rl-button--sm" href="#"><Icon class="rl-icon rl-icon--sm"/>Call</a><a class="rl-button rl-button--secondary rl-button--sm" href="#"><Icon class="rl-icon rl-icon--sm"/>Message</a></div>
</div></section>
<div class="rl-app__cols">
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Membership</h2></div><div class="rl-pass">
  <div class="rl-pass__top"><span class="rl-status rl-status--active">Active</span><span class="rl-pass__plan">Premium Plan</span><a class="rl-pass__link" href="#">Manage<Icon class="rl-icon rl-icon--xs"/></a></div>
  <p class="rl-figure">23 <small>days remaining</small></p>
  <span class="rl-bar" role="img" aria-label="68 of 91 days used"><span class="rl-bar__fill" style="--v:0.747"></span></span>
  <div class="rl-pass__dates"><span>29 Jul 2026</span><span>Expires 28 Oct 2026</span></div>
  <div class="rl-sub"><span><strong>Personal training:</strong> 9 of 12 sessions used</span><span class="rl-bar" role="img" aria-label="9 of 12 sessions used"><span class="rl-bar__fill" style="--v:0.750"></span></span></div>
</div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Next session</h2></div><div class="rl-card rl-session">
  <div class="rl-session__when"><div><p class="rl-session__time">9:00 AM</p><p class="rl-row__meta">Today, Personal Training, 45 min</p></div><span class="rl-pill rl-pill--soft"><Icon class="rl-icon rl-icon--xs"/>In 20 min</span></div>
  <div class="rl-session__who"><span class="rl-photo" aria-hidden="true">AR</span><span><span class="rl-row__title">Trainer: Arjun</span><span class="rl-row__meta">Focus: Back &amp; Biceps</span></span><a class="rl-button rl-button--secondary rl-button--sm" href="#">View Session</a></div>
</div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Attendance</h2><a class="rl-link" href="#"><span>View all</span></a></div><div class="rl-card rl-card--pad">
  <p class="rl-row__title">Checked in 9 days in a row</p><p class="rl-row__meta">25 check-ins in the last 30 days</p>
  <ol class="rl-week" aria-label="Last week"><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Mon</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Tue</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Wed</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Thu</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Fri</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Sat</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Sun</li></ol>
</div></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Payments</h2><a class="rl-link" href="#"><span>View all</span></a></div><div class="rl-card">
  <div style="padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--line)"><p class="rl-statusline"><span class="rl-sheet__check" style="width:24px;height:24px"><Icon class="rl-icon rl-icon--xs"/></span>No balance due</p></div>
  <ul class="rl-activity"><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__title">Premium Plan, 3 months</p><p class="rl-row__meta">29 Jul 2026, UPI</p></div><span class="rl-activity__amount">₹9,000</span></div></li><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__title">Personal training, 12 sessions</p><p class="rl-row__meta">29 Jul 2026, UPI</p></div><span class="rl-activity__amount">₹6,000</span></div></li></ul>
</div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Details</h2></div><div class="rl-card rl-card--pad"><dl class="rl-facts"><dt>Phone</dt><dd>+91 90000 12041</dd><dt>Email</dt><dd>rahul.kumar@example.com</dd><dt>Member since</dt><dd>29 Jul 2026</dd><dt>Trainer</dt><dd>Arjun Rao</dd><dt>Goal</dt><dd>Fat Loss</dd></dl></div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Notes</h2><a class="rl-link" href="#"><span>Add note</span></a></div><ul class="rl-card rl-notes"><li><p class="rl-row__body">Prefers morning sessions before work.</p><p class="rl-row__meta">Arjun Rao, 22 Sep</p></li><li><p class="rl-row__body">Asked about moving to the annual plan at renewal.</p><p class="rl-row__meta">Alex D’Souza, 1 Oct</p></li></ul></section></div>
</div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#" data-back><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Members</a><button class="rl-fab" type="button" data-sheet="pd-create" aria-haspopup="dialog" aria-expanded="false" aria-label="Create"><Icon class="rl-icon"/></button><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Attendance</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>
<div class="rl-sheet" id="pd-more" role="dialog" aria-modal="true" aria-labelledby="pd-more-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="pd-more-title">Member actions</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Edit Details</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Freeze Membership</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Send Renewal Reminder</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Note</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<div class="rl-sheet" id="pd-create" role="dialog" aria-modal="true" aria-labelledby="pd-create-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="pd-create-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Check In</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Member</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Collect Payment</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Subscription</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
</div>
```
