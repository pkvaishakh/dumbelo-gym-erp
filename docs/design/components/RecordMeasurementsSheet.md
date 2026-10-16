# RecordMeasurementsSheet

A trainer recording measurements: weight, waist, chest and arms side by side, any of them. Saving adds "Measured today: 82.5 kg, waist 91 cm" to the Training card. At least one is needed.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-mprofile="trainer" data-member-id="RL-1723">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Member</h1>
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-sheet="mt-more" aria-haspopup="dialog" aria-label="More actions"><Icon class="rl-icon"/></button>
</div></header>
<main class="rl-app__main">
<div class="rl-identity"><span class="rl-photo rl-photo--xl" aria-hidden="true">FA</span><div class="rl-identity__text"><h2 class="rl-identity__name">Farhan Ali</h2><p class="rl-identity__meta" style="margin:0"><span>RL-1723</span><span class="rl-status rl-status--due">Payment due</span></p></div></div>
<section class="rl-section" aria-label="Actions"><div class="rl-actions"><button class="rl-button" type="button" data-mp="log">Log Workout</button><button class="rl-button rl-button--secondary" type="button" data-mp="schedule">Schedule</button><div class="rl-actions__contact"><a class="rl-button rl-button--secondary rl-button--sm" href="tel:+919000011723"><Icon class="rl-icon rl-icon--sm"/>Call</a><a class="rl-button rl-button--secondary rl-button--sm" href="sms:+919000011723"><Icon class="rl-icon rl-icon--sm"/>Message</a></div></div></section>
<div class="rl-app__cols">
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Next session</h2></div><div class="rl-card rl-session">
  <div class="rl-session__when"><div><p class="rl-session__time">11:00 AM</p><p class="rl-row__meta">Mon 5 Oct, Personal Training, 45 min</p></div></div>
  <div class="rl-session__who"><span class="rl-photo" aria-hidden="true">AR</span><span><span class="rl-row__title">Full body</span><span class="rl-row__meta">Goal: Weight loss</span></span><a class="rl-button rl-button--secondary rl-button--sm" href="#" data-mp="session">View Session</a></div>
</div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Training</h2></div><div class="rl-card rl-card--pad"><dl class="rl-facts"><dt>Goal</dt><dd>Weight loss</dd><dt>Plan</dt><dd>Week 10 of 13</dd><dt>Last check-in</dt><dd>Today, 8:21 AM</dd></dl><div class="rl-sub" style="margin-top:var(--space-3)"><span><strong>Personal training:</strong> 7 of 12 sessions used</span><span class="rl-bar" role="img" aria-label="7 of 12 sessions used"><span class="rl-bar__fill" style="--v:0.583"></span></span></div><p class="rl-statusline" style="color:var(--attention);margin-top:var(--space-3)"><Icon class="rl-icon rl-icon--sm"/>Missed 2 sessions this week</p></div></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Membership</h2></div><div class="rl-pass">
  <div class="rl-pass__top"><span class="rl-status rl-status--due">Payment due</span><span class="rl-pass__plan">Monthly Plan</span></div>
  <p class="rl-figure">27 <small>days remaining</small></p>
  <span class="rl-bar" role="img" aria-label="10% of the plan used"><span class="rl-bar__fill" style="--v:0.097"></span></span>
  <div class="rl-pass__dates"><span>1 Oct 2026</span><span>Expires 31 Oct 2026</span></div>
  <div class="rl-sub"><span><strong>Personal training:</strong> 7 of 12 sessions used</span><span class="rl-bar" role="img" aria-label="7 of 12 sessions used"><span class="rl-bar__fill" style="--v:0.583"></span></span></div>
</div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Attendance</h2></div><div class="rl-card rl-card--pad"><p class="rl-row__title">Last check-in: Today, 8:21 AM</p><p class="rl-row__meta">14 check-ins in the last 30 days</p></div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Details</h2></div><div class="rl-card rl-card--pad"><dl class="rl-facts"><dt>Phone</dt><dd>+91 90000 11723</dd><dt>Member since</dt><dd>1 Dec 2025</dd></dl></div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Notes</h2><a class="rl-link" href="#"><span>Add note</span></a></div><div class="rl-card rl-card--pad"><p class="rl-row__meta" style="margin:0">No notes yet.</p></div></section></div>
</div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#" data-back><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Schedule</a><button class="rl-fab" type="button" data-sheet="mt-create" aria-haspopup="dialog" aria-expanded="false" aria-label="Create"><Icon class="rl-icon"/></button><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Members</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>
<div class="rl-sheet" id="mt-more" role="dialog" aria-modal="true" aria-labelledby="mt-more-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="mt-more-title">Member actions</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Assign Plan</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Record Measurements</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Book Session</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Note</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<div class="rl-sheet" id="mt-create" role="dialog" aria-modal="true" aria-labelledby="mt-create-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="mt-create-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Log Workout</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Note</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Record Measurements</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Assign Plan</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Book Session</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
</div><div class="rl-root rl-actlayer" data-actlayer>
<div class="rl-scrim is-open" data-close></div>
<div class="rl-sheet" id="ac-note" role="dialog" aria-modal="true" aria-labelledby="ac-note-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="ac-note-title">Add Note</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-sheet__who"><span class="rl-photo" aria-hidden="true" data-a="initials">FA</span><span><span class="rl-row__title" data-a="name">Farhan Ali</span><span class="rl-row__meta" data-a="meta">RL-1723 • Monthly Plan</span></span></div>
  <div class="rl-field" style="margin-top:var(--space-4)">
    <label class="rl-field__label" for="ac-note-text">Note</label>
    <div class="rl-field__control rl-field__control--area"><textarea class="rl-field__input" id="ac-note-text" name="ac-note-text" rows="3" placeholder="For example, prefers evening sessions"></textarea></div>
    <p class="rl-field__error" role="alert" hidden><Icon/><span>Write the note first</span></p>
    <p class="rl-field__hint">Staff at your gym can read notes. Members can’t.</p>
  </div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-a-save="note">Save Note</button></div>
</div>
<div class="rl-sheet" id="ac-freeze" role="dialog" aria-modal="true" aria-labelledby="ac-freeze-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="ac-freeze-title">Freeze Membership</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-sheet__who"><span class="rl-photo" aria-hidden="true" data-a="initials">FA</span><span><span class="rl-row__title" data-a="name">Farhan Ali</span><span class="rl-row__meta" data-a="meta">RL-1723 • Monthly Plan</span></span></div>
  <fieldset class="rl-fieldset" style="margin-top:var(--space-4)"><legend>Reason</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Travel" checked><span>Travel</span></label><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Illness or injury"><span>Illness or injury</span></label><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Exams"><span>Exams</span></label><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Other"><span>Other</span></label></div></fieldset>
  <fieldset class="rl-fieldset" style="margin-top:var(--space-4)"><legend>Freeze for</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="ac-weeks" value="1" checked><span>1 week</span></label><label class="rl-chipopt"><input type="radio" name="ac-weeks" value="2"><span>2 weeks</span></label><label class="rl-chipopt"><input type="radio" name="ac-weeks" value="4"><span>4 weeks</span></label></div></fieldset>
  <p class="rl-sheet__note" data-a="freezetext">Check-in is paused from today until 12 Oct. The plan will now end on 7 Nov 2026.</p>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-a-save="freeze">Freeze Membership</button></div>
</div>
<div class="rl-sheet" id="ac-unfreeze" data-modal role="alertdialog" aria-modal="true" aria-labelledby="ac-unfreeze-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="ac-unfreeze-title">Unfreeze <span data-a="name">Farhan Ali</span>?</h2><p class="rl-confirm__text">They can check in again from today. The days they did not use stay added to the end of the plan.</p></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-a-save="unfreeze">Unfreeze</button><button class="rl-button rl-button--secondary rl-button--bl
<!-- …trimmed -->
```
