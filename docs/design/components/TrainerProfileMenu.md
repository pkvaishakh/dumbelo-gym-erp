# TrainerProfileMenu

Trainer Home with the profile menu open, after tapping the avatar.

A sheet titled with the trainer's name: My Profile, My Availability, Settings, Sign Out. Every role's avatar opens the same kind of menu, with the rows that role needs. See Sheet.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root">
<header class="rl-appbar"><div class="rl-appbar__in">
  <a class="rl-logo" href="#" aria-label="Dumbelo home"><Mark/></a>
  <div class="rl-appbar__who"><h1 class="rl-appbar__hello">Good morning, Arjun 👋</h1><p class="rl-appbar__branch">Main Branch</p></div>
  <button class="rl-iconbtn" type="button" aria-label="Notifications, 2 unread"><Icon class="rl-icon"/><span class="rl-badge" aria-hidden="true">2</span></button>
  <button class="rl-avatar rl-pressable" type="button" data-sheet="rl-sheet-profile" aria-haspopup="dialog" aria-label="Profile menu: Arjun Rao">AR</button>
</div></header>
<main class="rl-app__main">
<div class="rl-app__cols" style="margin-top:var(--space-1)">
<div class="rl-app__col"><section class="rl-section" aria-label="Next session"><article class="rl-hero" data-when="next" aria-label="Next session">
  <div class="rl-hero__top"><p class="rl-hero__kicker">Next session</p><span class="rl-pill rl-pill--volt"><Icon class="rl-icon rl-icon--xs"/>Starts in 25 min</span></div>
  <p class="rl-figure">11:00 AM <small>Personal Training, 45 min</small></p>
  <div class="rl-hero__member"><span class="rl-photo rl-photo--lg" aria-hidden="true">RK</span><span><span class="rl-hero__name">Rahul Kumar</span><span class="rl-hero__tags"><span class="rl-pill rl-pill--on-ink">Fat Loss</span><span class="rl-pill rl-pill--on-ink">71.2 kg</span></span></span></div>
  <div><p class="rl-hero__kicker">Today’s workout</p><p class="rl-hero__title">Chest &amp; Triceps</p></div>
  <p class="rl-hero__note"><Icon class="rl-icon rl-icon--xs"/>Not checked in yet</p>
  <div class="rl-hero__actions"><button class="rl-button rl-button--accent" type="button" data-session="live">Start Session</button><a class="rl-button rl-button--on-ink" href="#">View Member</a></div>
</article>
<article class="rl-hero" data-when="live" hidden aria-label="Session in progress">
  <div class="rl-hero__top"><p class="rl-hero__kicker">Session in progress</p><span class="rl-pill rl-pill--volt"><Icon class="rl-icon rl-icon--xs"/>Started 11:00 AM</span></div>
  <p class="rl-figure">12 min <small>of 45 min</small></p>
  <span class="rl-bar" role="img" aria-label="12 of 45 minutes"><span class="rl-bar__fill" style="--v:0.267"></span></span>
  <div class="rl-hero__member"><span class="rl-photo rl-photo--lg" aria-hidden="true">RK</span><span><span class="rl-hero__name">Rahul Kumar</span><span class="rl-hero__tags"><span class="rl-pill rl-pill--on-ink">Fat Loss</span><span class="rl-pill rl-pill--on-ink">71.2 kg</span></span></span></div>
  <div><p class="rl-hero__kicker">Today’s workout</p><p class="rl-hero__title">Chest &amp; Triceps</p></div>
  <div class="rl-hero__actions"><button class="rl-button rl-button--accent" type="button" data-session="next">End Session</button><a class="rl-button rl-button--on-ink" href="#" data-open-session>Open Session</a></div>
</article></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Quick actions</h2></div><div class="rl-tiles"><button class="rl-tile rl-pressable" type="button"><Icon class="rl-icon"/><span>Mark Attendance</span></button><button class="rl-tile rl-pressable" type="button"><Icon class="rl-icon"/><span>Log Workout</span></button><button class="rl-tile rl-pressable" type="button"><Icon class="rl-icon"/><span>Add Note</span></button><button class="rl-tile rl-pressable" type="button"><Icon class="rl-icon"/><span>Record Measurements</span></button></div></section></div>
</div>
<section class="rl-section" aria-label="Today’s overview">
<div class="rl-scroller"><a class="rl-stat rl-pressable" href="#"><span class="rl-stat__icon"><Icon class="rl-icon rl-icon--sm"/></span><p class="rl-stat__value">6</p><p class="rl-stat__label">Sessions today</p><p class="rl-stat__note">2 done, 4 to go</p></a><a class="rl-stat rl-pressable" href="#"><span class="rl-stat__icon"><Icon class="rl-icon rl-icon--sm"/></span><p class="rl-stat__value">18</p><p class="rl-stat__label">My members</p></a><a class="rl-stat rl-pressable" href="#"><span class="rl-stat__icon"><Icon class="rl-icon rl-icon--sm"/></span><p class="rl-stat__value">5</p><p class="rl-stat__label">Checked in today</p><p class="rl-stat__note">Of my members</p></a><a class="rl-stat rl-pressable" href="#"><span class="rl-stat__icon"><Icon class="rl-icon rl-icon--sm"/></span><p class="rl-stat__value">4</p><p class="rl-stat__label">Need attention</p></a></div>
</section>
<div class="rl-app__cols">
<div class="rl-app__col">
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Today’s schedule</h2><a class="rl-link" href="#"><span>View all</span></a></div><div class="rl-card" style="overflow:hidden">
  <div class="rl-agenda__summary"><span><strong>2 of 6 sessions done</strong> today</span><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.333"></span></span></div>
  <ul class="rl-agenda"><li><a class="rl-agenda__row is-now" href="#"><span class="rl-agenda__time">11:00 AM<br><span class="rl-tag rl-tag--next">Next</span></span><span><span class="rl-agenda__top"><span class="rl-tag">PT</span><span class="rl-row__title">Rahul Kumar</span></span><span class="rl-row__meta">Chest &amp; Triceps, 45 min</span></span></a></li><li><a class="rl-agenda__row" href="#"><span class="rl-agenda__time">12:30 PM</span><span><span class="rl-agenda__top"><span class="rl-tag">PT</span><span class="rl-row__title">Anjali Nair</span></span><span class="rl-row__meta">Upper body, 45 min</span></span></a></li><li><a class="rl-agenda__row" href="#"><span class="rl-agenda__time">5:00 PM</span><span><span class="rl-agenda__top"><span class="rl-tag">PT</span><span class="rl-row__title">Karthik Iyer</span></span><span class="rl-row__meta">Core and mobility, 45 min</span></span></a></li><li><a class="rl-agenda__row" href="#"><span class="rl-agenda__time">6:00 PM</span><span><span class="rl-agenda__top"><span class="rl-tag">Class</span><span class="rl-row__title">HIIT Burn</span></span><span class="rl-row__meta">13/20 booked</span></span></a></li></ul>
</div></section>
</div>
<div class="rl-app__col">
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Needs attention</h2><a class="rl-link" href="#"><span>View all</span></a></div><ul class="rl-attn"><li><a class="rl-attn__row" href="#"><span class="rl-photo" aria-hidden="true">FA</span><span class="rl-attn__text"><span class="rl-row__title">Farhan Ali</span><span class="rl-row__meta">Missed 2 sessions this week</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li><li><a class="rl-attn__row" href="#"><span class="rl-photo" aria-hidden="true">DM</span><span class="rl-attn__text"><span class="rl-row__title">Deepa Menon</span><span class="rl-row__meta">No check-in for 9 days</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li><li><a class="rl-attn__row" href="#"><span class="rl-photo" aria-hidden="true">KI</span><span class="rl-attn__text"><span class="rl-row__title">Karthik Iyer</span><span class="rl-row__meta">Membership ends tomorrow</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li><li><a class="rl-attn__row" href="#"><span class="rl-photo" aria-hidden="true">AN</span><span class="rl-attn__text"><span class="rl-row__title">Anjali Nair</span><span class="rl-row__meta">Measurements due this week</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li></ul></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">My members’ activity</h2><a class="rl-link" href="#"><span>View all</span></a></div><ul class="rl-card rl-activity"><li><div class="rl-activity__row"><span class="rl-photo" aria-hidden="true">TB</span><div class="rl-activity__text"><p class="rl-row__body"><strong>Tara Bose</strong> finished Legs, 45 min</p><p class="rl-row__meta">1 h 20 min ago</p></div></div></li><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__body"><strong>Rahul Kumar</strong> logged 71.2 kg</p><p class="rl-row__meta">1 h 30 min ago</p></div></div></li><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__body"><strong>You</strong> updated Rahul Kumar’s plan</p><p class="rl-row__meta">2 h 20 min ago</p></div></div></li><li><div class="rl-activity__row"><span class="rl-photo" aria-hidden="true">MS</span><div class="rl-activity__text"><p class="rl-row__body"><strong>Meenal Shah</strong> finished Full body, 45 min</p><p class="rl-row__meta">2 h 50 min ago</p></div></div></li></ul></section>
</div>
</div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Schedule</a><button class="rl-fab" type="button" data-sheet="rl-sheet-tcreate" aria-haspopup="dialog" aria-expanded="false" aria-label="Create"><Icon class="rl-icon"/></button><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Members</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim is-open" data-close></div>
<div class="rl-sheet" id="rl-sheet-tcreate" role="dialog" aria-modal="true" aria-labelledby="rl-sheet-tcreate-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="rl-sheet-tcreate-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Log Workout</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Note</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Record Measurements</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Assign Plan</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Book Session</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<div class="rl-sheet is-open" id="rl-sheet-profile" role="dialog" aria-modal="true" aria-labelledby="rl-sheet-profile-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="rl-sheet-profile-title">Arjun Rao</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">My Profile</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">My Availability</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></l
<!-- …trimmed -->
```
