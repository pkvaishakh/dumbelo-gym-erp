# FreezeSheet

Freezing a membership: a reason (Travel, Illness or injury, Exams, Other) and how long (1, 2 or 4 weeks). One line spells out the result before anything is saved: "Check-in is paused from today until 19 Oct. The plan will now end on 17 Mar 2027."

After saving, the profile's badge and card read Frozen, and Check In is replaced by the paused line and Unfreeze.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-mprofile="desk" data-member-id="RL-2210">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Member</h1>
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-sheet="mp-more" aria-haspopup="dialog" aria-label="More actions"><Icon class="rl-icon"/></button>
</div></header>
<main class="rl-app__main">
<div class="rl-identity"><span class="rl-photo rl-photo--xl" aria-hidden="true">SK</span><div class="rl-identity__text"><h2 class="rl-identity__name">Sana Kapoor</h2><p class="rl-identity__meta" style="margin:0"><span>RL-2210</span><span class="rl-status rl-status--active">Active</span></p></div></div>
<section class="rl-section" aria-label="Actions"><div class="rl-actions"><button class="rl-button" type="button" data-mp="checkin" hidden>Check In</button><p class="rl-statusline" data-mp-in  style="align-self:center"><span class="rl-sheet__check" style="width:24px;height:24px"><Icon class="rl-icon rl-icon--xs"/></span><span data-mp-in-text>Checked in at 8:38 AM</span></p><a class="rl-button rl-button--secondary" href="#" data-mp="collect">Collect Payment</a><div class="rl-actions__contact"><a class="rl-button rl-button--secondary rl-button--sm" href="tel:+919000012210"><Icon class="rl-icon rl-icon--sm"/>Call</a><a class="rl-button rl-button--secondary rl-button--sm" href="sms:+919000012210"><Icon class="rl-icon rl-icon--sm"/>Message</a></div></div></section>
<div class="rl-app__cols">
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Membership</h2></div><div class="rl-pass">
  <div class="rl-pass__top"><span class="rl-status rl-status--active">Active</span><span class="rl-pass__plan">Annual Plan</span><a class="rl-pass__link" href="#" data-mp="renew">Manage<Icon class="rl-icon rl-icon--xs"/></a></div>
  <p class="rl-figure">149 <small>days remaining</small></p>
  <span class="rl-bar" role="img" aria-label="59% of the plan used"><span class="rl-bar__fill" style="--v:0.589"></span></span>
  <div class="rl-pass__dates"><span>4 Mar 2026</span><span>Expires 3 Mar 2027</span></div>
  
</div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Attendance</h2><a class="rl-link" href="#" data-mp="attendance"><span>View all</span></a></div><div class="rl-card rl-card--pad"><p class="rl-row__title">Last check-in: Today, 8:38 AM</p><p class="rl-row__meta">16 check-ins in the last 30 days</p></div></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Payments</h2></div><div class="rl-card"><div style="padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--line)"><p class="rl-statusline"><span class="rl-sheet__check" style="width:24px;height:24px"><Icon class="rl-icon rl-icon--xs"/></span>No balance due</p></div><ul class="rl-activity"><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__title">Annual Plan, 12 months</p><p class="rl-row__meta">4 Mar 2026, UPI</p></div><span class="rl-activity__amount">₹15,000</span></div></li></ul></div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Details</h2></div><div class="rl-card rl-card--pad"><dl class="rl-facts"><dt>Phone</dt><dd>+91 90000 12210</dd><dt>Email</dt><dd>sana.kapoor@mail.example</dd><dt>Member since</dt><dd>4 Mar 2026</dd><dt>Trainer</dt><dd>None assigned</dd><dt>Goal</dt><dd>General fitness</dd></dl></div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Notes</h2><a class="rl-link" href="#"><span>Add note</span></a></div><div class="rl-card rl-card--pad"><p class="rl-row__meta" style="margin:0">No notes yet.</p></div></section></div>
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
</div><div class="rl-root rl-actlayer" data-actlayer>
<div class="rl-scrim is-open" data-close></div>
<div class="rl-sheet" id="ac-note" role="dialog" aria-modal="true" aria-labelledby="ac-note-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="ac-note-title">Add Note</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-sheet__who"><span class="rl-photo" aria-hidden="true" data-a="initials">SK</span><span><span class="rl-row__title" data-a="name">Sana Kapoor</span><span class="rl-row__meta" data-a="meta">RL-2210 • Annual Plan</span></span></div>
  <div class="rl-field" style="margin-top:var(--space-4)">
    <label class="rl-field__label" for="ac-note-text">Note</label>
    <div class="rl-field__control rl-field__control--area"><textarea class="rl-field__input" id="ac-note-text" name="ac-note-text" rows="3" placeholder="For example, prefers evening sessions"></textarea></div>
    <p class="rl-field__error" role="alert" hidden><Icon/><span>Write the note first</span></p>
    <p class="rl-field__hint">Staff at your gym can read notes. Members can’t.</p>
  </div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-a-save="note">Save Note</button></div>
</div>
<div class="rl-sheet is-open" id="ac-freeze" role="dialog" aria-modal="true" aria-labelledby="ac-freeze-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="ac-freeze-title">Freeze Membership</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-sheet__who"><span class="rl-photo" aria-hidden="true" data-a="initials">SK</span><span><span class="rl-row__title" data-a="name">Sana Kapoor</span><span class="rl-row__meta" data-a="meta">RL-2210 • Annual Plan</span></span></div>
  <fieldset class="rl-fieldset" style="margin-top:var(--space-4)"><legend>Reason</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Travel" checked><span>Travel</span></label><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Illness or injury"><span>Illness or injury</span></label><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Exams"><span>Exams</span></label><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Other"><span>Other</span></label></div></fieldset>
  <fieldset class="rl-fieldset" style="margin-top:var(--space-4)"><legend>Freeze for</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="ac-weeks" value="1" checked><span>1 week</span></label><label class="rl-chipopt"><input type="radio" name="ac-weeks" value="2"><span>2 weeks</span></label><label class="rl-chipopt"><input type="radio" name="ac-weeks" value="4"><span>4 weeks</span></label></div></fieldset>
  <p class="rl-sheet__note" data-a="freezetext">Check-in is paused from today until 12 Oct. The plan will now end on 10 Mar 2027.</p>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-a-save="freeze">Freeze Membership</button></div>
</div>
<div class="rl-sheet" id="ac-unfreeze" data-modal role="alertdialog" aria-modal="true" aria-labelledby="ac-unfreeze-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="ac-unfreeze-title">Unfreeze <span data-a="name">Sana Kapoor</span>?</h2><p class="rl-confirm__text">They can check in again from today. The days they did not use stay added to the end of the plan.</p></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-a-save="unfreeze">Unfreeze</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-close>Keep Frozen</button></div>
</div>
<div class="rl-sheet" id="ac-remind" role="dialog" aria-modal="true" aria-labelledby="ac-remind-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="ac-remind-title">Send Renewal Reminder</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-sheet__who"><span 
<!-- …trimmed -->
```
