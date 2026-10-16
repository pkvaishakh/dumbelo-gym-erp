# MemberHomeWide

Member Home from 768px: the same screen in a centred 960px container, with no sidebar.

Identical markup to MemberHome. From 768px the sections flow into two columns: membership, today's plan and the upcoming session on the left; today's progress, the streak, recent progress and reminders on the right. The bottom navigation stays at the bottom with its five tabs centred.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-avatar rl-pressable" type="button" aria-label="Your profile: Rahul Kumar">RK</button>
  <div class="rl-appbar__who" style="margin-left:var(--space-1)"><h1 class="rl-appbar__hello">Good morning, Rahul 👋</h1><p class="rl-appbar__branch">Main Branch</p></div>
  <button class="rl-iconbtn" type="button" aria-label="Notifications, 2 unread"><Icon class="rl-icon"/><span class="rl-badge" aria-hidden="true">2</span></button>
</div></header>
<main class="rl-app__main">
<div class="rl-app__cols">
<div class="rl-app__col">
<section class="rl-section" aria-label="Membership" style="margin-top:var(--space-1)"><a class="rl-pass rl-pressable" href="#" aria-label="Premium Plan, active, 24 days remaining. View membership">
  <span class="rl-pass__top"><span class="rl-status rl-status--active">Active</span><span class="rl-pass__plan">Premium Plan</span><span class="rl-pass__link">View Membership<Icon class="rl-icon rl-icon--xs"/></span></span>
  <p class="rl-figure">24 <small>days remaining</small></p>
  <span class="rl-bar" role="img" aria-label="67 of 91 days used"><span class="rl-bar__fill" style="--v:0.736"></span></span>
  <span class="rl-pass__dates"><span>29 Jul 2026</span><span>Expires 28 Oct 2026</span></span>
</a></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Today’s plan</h2></div><div class="rl-plan">
  <article class="rl-plan__card rl-plan__card--workout" data-when="todo">
    <p class="rl-plan__kicker">Today’s workout</p>
    <div class="rl-plan__art"><div class="rl-barbell rl-barbell--on-ink rl-barbell--bleed" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
    <h3 class="rl-plan__title">Chest &amp; Triceps</h3>
    <p class="rl-plan__meta"><span class="rl-pill rl-pill--on-ink">6 exercises</span><span class="rl-pill rl-pill--on-ink">45 min</span></p>
    <span class="rl-plan__spacer"></span>
    <button class="rl-button rl-button--accent rl-button--block" type="button" data-start>Start Workout</button>
  </article>
  <article class="rl-plan__card rl-plan__card--workout" data-when="done" hidden>
    <p class="rl-plan__kicker">Today’s workout</p>
    <div class="rl-plan__art"><div class="rl-barbell rl-barbell--on-ink rl-barbell--bleed" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
    <h3 class="rl-plan__title">Chest &amp; Triceps</h3>
    <p class="rl-plan__done"><span><Icon class="rl-icon rl-icon--xs"/></span>Completed</p>
    <p class="rl-plan__meta"><span class="rl-pill rl-pill--on-ink">6 of 6 exercises</span><span class="rl-pill rl-pill--on-ink">45 min</span></p>
    <span class="rl-plan__spacer"></span>
    <button class="rl-button rl-button--on-ink rl-button--block" type="button">View Summary</button>
  </article>
  <article class="rl-plan__card">
    <p class="rl-plan__kicker">Today’s diet</p>
    <span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span>
    <p class="rl-figure">2,350 <small>kcal</small></p>
    <p class="rl-plan__meta"><span class="rl-pill">Today’s target</span><span class="rl-pill">5 meals</span></p>
    <span class="rl-plan__spacer"></span>
    <a class="rl-button rl-button--secondary rl-button--block" href="#">View Diet</a>
  </article>
</div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Upcoming session</h2><a class="rl-link" href="#"><span>Book Session</span></a></div><div class="rl-card rl-session">
  <div class="rl-session__when"><div><p class="rl-session__time">11:00 AM</p><p class="rl-row__meta">Personal Training, 45 minutes</p></div><span class="rl-pill rl-pill--soft"><Icon class="rl-icon rl-icon--xs"/>In 1 h 45 min</span></div>
  <div class="rl-session__who"><span class="rl-photo" aria-hidden="true">AR</span><span><span class="rl-row__title">Trainer: Arjun</span><span class="rl-row__meta">Focus: Chest &amp; Triceps</span></span><a class="rl-button rl-button--secondary rl-button--sm" href="#">View Session</a></div>
</div></section>
</div>
<div class="rl-app__col">
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Today’s progress</h2></div><div class="rl-card rl-progress"><div class="rl-progress__item" data-when="todo"><span class="rl-ring rl-ring--empty" style="--v:0.000"><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Workout</span><span class="rl-progress__value">Not started</span></span></div><div class="rl-progress__item" data-when="done" hidden><span class="rl-ring" style="--v:1.000"><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Workout</span><span class="rl-progress__value">Done, 45 min</span></span></div><div class="rl-progress__item"><span class="rl-ring" style="--v:0.221"><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Calories eaten</span><span class="rl-progress__value">520 / 2,350 kcal</span></span></div><div class="rl-progress__item"><span class="rl-ring" style="--v:0.250" data-water-v><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Water</span><span class="rl-progress__value" data-water-text>0.75 / 3 L</span></span><button class="rl-progress__add" type="button" data-sheet="rl-sheet-water" aria-haspopup="dialog" aria-label="Log water"><Icon class="rl-icon rl-icon--sm"/></button></div><div class="rl-progress__item"><span class="rl-ring" style="--v:0.355"><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Steps</span><span class="rl-progress__value">2,840 / 8,000</span></span></div></div></section>
<section class="rl-streak" aria-label="Attendance streak">
  <h2 class="rl-streak__title">🔥 8 Day Streak</h2>
  <p class="rl-streak__text">You’ve checked in 8 days in a row. Check in today to make it 9.</p>
  <ol class="rl-week" aria-label="This week"><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Mon</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Tue</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Wed</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Thu</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Fri</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Sat</li><li class="is-today"><span class="rl-week__dot" aria-label="Not checked in yet"></span>Today</li></ol>
</section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Recent progress</h2><a class="rl-link" href="#"><span>View Progress</span></a></div><div class="rl-card rl-weight">
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
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Reminders</h2></div><ul class="rl-card rl-remind"><li><a class="rl-remind__row" href="#"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-remind__text"><span class="rl-row__body">Arjun updated your workout plan</span><span class="rl-row__meta">1 h ago</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li><li><a class="rl-remind__row" href="#"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-remind__text"><span class="rl-row__body">Record your weekly measurements</span><span class="rl-row__meta">2 h ago</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li><li><a class="rl-remind__row" href="#"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-remind__text"><span class="rl-row__body">Your diet plan for next week is ready</span><span class="rl-row__meta">Yesterday</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li></ul></section>
</div>
</div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Workout</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Diet</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Progress</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>
<div class="rl-sheet" id="rl-sh
<!-- …trimmed -->
```
