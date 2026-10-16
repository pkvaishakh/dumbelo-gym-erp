# MemberProfileTrainer

The Member Profile as the member's trainer sees it.

Same screen, different sections. The actions are "Log Workout", which opens the LogWorkout task with this member filled in, and "Add Note". Progress (current weight, change and the eight-week chart) and Training (goal, plan week, last workout, sessions used) replace Payments. The membership card is read-only, without a Manage link, so the trainer knows if it is about to lapse. No payments, balances or prices.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Member</h1>
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-sheet="pt-more" aria-haspopup="dialog" aria-label="More actions"><Icon class="rl-icon"/></button>
</div></header>
<main class="rl-app__main">
<div class="rl-identity"><span class="rl-photo rl-photo--xl" aria-hidden="true">RK</span><div class="rl-identity__text"><h2 class="rl-identity__name">Rahul Kumar</h2><p class="rl-identity__meta" style="margin:0"><span>RL-2041</span><span class="rl-status rl-status--active">Active</span></p></div></div>
<section class="rl-section" aria-label="Actions"><div class="rl-actions">
  <button class="rl-button" type="button">Log Workout</button>
  <button class="rl-button rl-button--secondary" type="button">Add Note</button>
  <div class="rl-actions__contact"><a class="rl-button rl-button--secondary rl-button--sm" href="#"><Icon class="rl-icon rl-icon--sm"/>Call</a><a class="rl-button rl-button--secondary rl-button--sm" href="#"><Icon class="rl-icon rl-icon--sm"/>Message</a></div>
</div></section>
<div class="rl-app__cols">
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Next session</h2></div><div class="rl-card rl-session">
  <div class="rl-session__when"><div><p class="rl-session__time">11:00 AM</p><p class="rl-row__meta">Today, Personal Training, 45 min</p></div><span class="rl-pill rl-pill--soft"><Icon class="rl-icon rl-icon--xs"/>In 24 min</span></div>
  <div class="rl-session__who"><span class="rl-photo" aria-hidden="true">AR</span><span><span class="rl-row__title">Chest &amp; Triceps</span><span class="rl-row__meta">Not checked in yet</span></span><a class="rl-button rl-button--secondary rl-button--sm" href="#">View Session</a></div>
</div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Progress</h2><a class="rl-link" href="#"><span>View all</span></a></div><div class="rl-card rl-weight">
  <div class="rl-weight__top">
    <div><p class="rl-figure">71.2 <small>kg</small></p><p class="rl-row__meta">Updated today</p></div>
    <div class="rl-weight__side"><span class="rl-pill rl-pill--soft"><Icon class="rl-icon rl-icon--xs"/>−4.8 kg, on track</span><span class="rl-row__meta">Started at 76.0 kg</span></div>
  </div>
  <div class="rl-chart rl-chart--sm" role="group" aria-label="Weight in kilograms, last 8 weeks">
    <div class="rl-chart__y" aria-hidden="true"><span style="--p:0">70</span><span style="--p:0.5">73</span><span style="--p:1">76</span></div>
    <div class="rl-chart__plot"><div class="rl-chart__grid" aria-hidden="true"><span style="--p:0"></span><span style="--p:0.5"></span><span style="--p:1"></span></div><Icon class="rl-chart__line"/><span class="rl-chart__dot" style="--x:0.9375;--v:0.2000"></span><span class="rl-chart__marker"></span><div class="rl-chart__cols"><button class="rl-chart__col" type="button" style="--v:0.6833;--x:0.0625" data-label="Sun 16 Aug" data-value="74.1 kg" aria-label="Sun 16 Aug: 74.1 kg"></button><button class="rl-chart__col" type="button" style="--v:0.6333;--x:0.1875" data-label="Sun 23 Aug" data-value="73.8 kg" aria-label="Sun 23 Aug: 73.8 kg"></button><button class="rl-chart__col" type="button" style="--v:0.5333;--x:0.3125" data-label="Sun 30 Aug" data-value="73.2 kg" aria-label="Sun 30 Aug: 73.2 kg"></button><button class="rl-chart__col" type="button" style="--v:0.5000;--x:0.4375" data-label="Sun 6 Sep" data-value="73.0 kg" aria-label="Sun 6 Sep: 73.0 kg"></button><button class="rl-chart__col" type="button" style="--v:0.4000;--x:0.5625" data-label="Sun 13 Sep" data-value="72.4 kg" aria-label="Sun 13 Sep: 72.4 kg"></button><button class="rl-chart__col" type="button" style="--v:0.3500;--x:0.6875" data-label="Sun 20 Sep" data-value="72.1 kg" aria-label="Sun 20 Sep: 72.1 kg"></button><button class="rl-chart__col" type="button" style="--v:0.2667;--x:0.8125" data-label="Sun 27 Sep" data-value="71.6 kg" aria-label="Sun 27 Sep: 71.6 kg"></button><button class="rl-chart__col" type="button" style="--v:0.2000;--x:0.9375" data-label="Sun 4 Oct" data-value="71.2 kg" aria-label="Sun 4 Oct: 71.2 kg"></button></div><div class="rl-chart__tip" role="status"></div></div>
    <div class="rl-chart__x rl-chart__x--free"><span style="--x:0.0625">16 Aug</span><span style="--x:0.4375">6 Sep</span><span style="--x:0.9375">4 Oct</span></div>
  </div>
</div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Training</h2></div><div class="rl-card rl-card--pad"><dl class="rl-facts"><dt>Goal</dt><dd>Fat Loss</dd><dt>Plan</dt><dd>Week 10 of 13</dd><dt>Last workout</dt><dd>Thu 1 Oct, Back &amp; Biceps</dd></dl><div class="rl-sub" style="margin-top:var(--space-3)"><span><strong>Personal training:</strong> 8 of 12 sessions used</span><span class="rl-bar" role="img" aria-label="8 of 12 sessions used"><span class="rl-bar__fill" style="--v:0.667"></span></span></div></div></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Membership</h2></div><div class="rl-pass">
  <div class="rl-pass__top"><span class="rl-status rl-status--active">Active</span><span class="rl-pass__plan">Premium Plan</span></div>
  <p class="rl-figure">24 <small>days remaining</small></p>
  <span class="rl-bar" role="img" aria-label="67 of 91 days used"><span class="rl-bar__fill" style="--v:0.736"></span></span>
  <div class="rl-pass__dates"><span>29 Jul 2026</span><span>Expires 28 Oct 2026</span></div>
</div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Attendance</h2><a class="rl-link" href="#"><span>View all</span></a></div><div class="rl-card rl-card--pad">
  <p class="rl-row__title">Checked in 8 days in a row</p><p class="rl-row__meta">24 check-ins in the last 30 days</p>
  <ol class="rl-week" aria-label="This week"><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Mon</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Tue</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Wed</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Thu</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Fri</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Sat</li><li class="is-today"><span class="rl-week__dot" aria-label="Not checked in yet"></span>Today</li></ol>
</div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Details</h2></div><div class="rl-card rl-card--pad"><dl class="rl-facts"><dt>Phone</dt><dd>+91 90000 12041</dd><dt>Member since</dt><dd>29 Jul 2026</dd><dt>Started at</dt><dd>76.0 kg</dd></dl></div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Notes</h2><a class="rl-link" href="#"><span>Add note</span></a></div><ul class="rl-card rl-notes"><li><p class="rl-row__body">Prefers morning sessions before work.</p><p class="rl-row__meta">Arjun Rao, 22 Sep</p></li><li><p class="rl-row__body">Asked about moving to the annual plan at renewal.</p><p class="rl-row__meta">Alex D’Souza, 1 Oct</p></li></ul></section></div>
</div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#" data-back><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Schedule</a><button class="rl-fab" type="button" data-sheet="pt-create" aria-haspopup="dialog" aria-expanded="false" aria-label="Create"><Icon class="rl-icon"/></button><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Members</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>
<div class="rl-sheet" id="pt-more" role="dialog" aria-modal="true" aria-labelledby="pt-more-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="pt-more-title">Member actions</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Assign Plan</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Record Measurements</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Book Session</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Note</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<div class="rl-sheet" id="pt-create" role="dialog" aria-modal="true" aria-labelledby="pt-create-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="pt-create-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Log Workout</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Note</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Record Measurements</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Assign Plan</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Book Session</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
</div>
```
