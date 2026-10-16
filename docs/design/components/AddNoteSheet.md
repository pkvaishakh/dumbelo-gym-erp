# AddNoteSheet

Adding a note to a member, from the ⋮ menu or the Add note link on their profile.

A sheet: the member's card at the top, one TextArea, a line saying who can read it, and Save Note. The note goes to the top of the profile's Notes with the writer's name and "just now".

- Every member-action sheet starts with the same member card (`rl-sheet__who`), so staff never act on the wrong person.
- Related: AddNoteSheetError, MemberPickerSheet.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-mprofile="desk" data-member-id="RL-1688">
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Member</h1>
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-sheet="mp-more" aria-haspopup="dialog" aria-label="More actions"><Icon class="rl-icon"/></button>
</div></header>
<main class="rl-app__main">
<div class="rl-identity"><span class="rl-photo rl-photo--xl" aria-hidden="true">KI</span><div class="rl-identity__text"><h2 class="rl-identity__name">Karthik Iyer</h2><p class="rl-identity__meta" style="margin:0"><span>RL-1688</span><span class="rl-status rl-status--expiring">Expiring</span></p></div></div>
<section class="rl-section" aria-label="Actions"><div class="rl-actions"><button class="rl-button" type="button" data-mp="checkin" hidden>Check In</button><p class="rl-statusline" data-mp-in  style="align-self:center"><span class="rl-sheet__check" style="width:24px;height:24px"><Icon class="rl-icon rl-icon--xs"/></span><span data-mp-in-text>Checked in at 8:09 AM</span></p><a class="rl-button rl-button--secondary" href="#" data-mp="collect">Collect Payment</a><div class="rl-actions__contact"><a class="rl-button rl-button--secondary rl-button--sm" href="tel:+919000011688"><Icon class="rl-icon rl-icon--sm"/>Call</a><a class="rl-button rl-button--secondary rl-button--sm" href="sms:+919000011688"><Icon class="rl-icon rl-icon--sm"/>Message</a></div></div></section>
<div class="rl-app__cols">
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Membership</h2></div><div class="rl-pass rl-pass--renew">
  <div class="rl-pass__top"><span class="rl-status rl-status--expiring">Expiring</span><span class="rl-pass__plan">Monthly Plan</span><a class="rl-pass__link" href="#" data-mp="renew">Manage<Icon class="rl-icon rl-icon--xs"/></a></div>
  <p class="rl-figure">Ends today</p>
  <span class="rl-bar" role="img" aria-label="97% of the plan used"><span class="rl-bar__fill" style="--v:0.967"></span></span>
  <div class="rl-pass__dates"><span>6 Sep 2026</span><span>Expires 5 Oct 2026</span></div>
  <div class="rl-sub"><span><strong>Personal training:</strong> 10 of 12 sessions used</span><span class="rl-bar" role="img" aria-label="10 of 12 sessions used"><span class="rl-bar__fill" style="--v:0.833"></span></span></div>
</div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Next session</h2></div><div class="rl-card rl-session">
  <div class="rl-session__when"><div><p class="rl-session__time">8:00 AM</p><p class="rl-row__meta">Tue 6 Oct, Personal Training, 45 min</p></div></div>
  <div class="rl-session__who"><span class="rl-photo" aria-hidden="true">AR</span><span><span class="rl-row__title">Trainer: Arjun</span><span class="rl-row__meta">Focus: Core and mobility</span></span><a class="rl-button rl-button--secondary rl-button--sm" href="#" data-mp="session">View Session</a></div>
</div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Attendance</h2><a class="rl-link" href="#" data-mp="attendance"><span>View all</span></a></div><div class="rl-card rl-card--pad"><p class="rl-row__title">Last check-in: Today, 8:09 AM</p><p class="rl-row__meta">10 check-ins in the last 30 days</p></div></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Payments</h2></div><div class="rl-card"><div style="padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--line)"><p class="rl-statusline"><span class="rl-sheet__check" style="width:24px;height:24px"><Icon class="rl-icon rl-icon--xs"/></span>No balance due</p></div><ul class="rl-activity"><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__title">Monthly Plan, 1 month</p><p class="rl-row__meta">6 Sep 2026, Card</p></div><span class="rl-activity__amount">₹1,500</span></div></li><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__title">Personal training, 12 sessions</p><p class="rl-row__meta">6 Sep 2026, Card</p></div><span class="rl-activity__amount">₹6,000</span></div></li></ul></div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Details</h2></div><div class="rl-card rl-card--pad"><dl class="rl-facts"><dt>Phone</dt><dd>+91 90000 11688</dd><dt>Email</dt><dd>karthik.iyer@mail.example</dd><dt>Member since</dt><dd>6 Sep 2025</dd><dt>Trainer</dt><dd>Arjun Rao</dd><dt>Goal</dt><dd>Mobility</dd></dl></div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Notes</h2><a class="rl-link" href="#"><span>Add note</span></a></div><div class="rl-card rl-card--pad"><p class="rl-row__meta" style="margin:0">No notes yet.</p></div></section></div>
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
<div class="rl-sheet is-open" id="ac-note" role="dialog" aria-modal="true" aria-labelledby="ac-note-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="ac-note-title">Add Note</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-sheet__who"><span class="rl-photo" aria-hidden="true" data-a="initials">KI</span><span><span class="rl-row__title" data-a="name">Karthik Iyer</span><span class="rl-row__meta" data-a="meta">RL-1688 • Monthly Plan</span></span></div>
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
  <div class="rl-sheet__who"><span class="rl-photo" aria-hidden="true" data-a="initials">KI</span><span><span class="rl-row__title" data-a="name">Karthik Iyer</span><span class="rl-row__meta" data-a="meta">RL-1688 • Monthly Plan</span></span></div>
  <fieldset class="rl-fieldset" style="margin-top:var(--space-4)"><legend>Reason</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Travel" checked><span>Travel</span></label><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Illness or injury"><span>Illness or injury</span></label><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Exams"><span>Exams</span></label><label class="rl-chipopt"><input type="radio" name="ac-reason" value="Other"><span>Other</span></label></div></fieldset>
  <fieldset class="rl-fieldset" style="margin-top:var(--space-4)"><legend>Freeze for</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="ac-weeks" value="1" checked><span>1 week</span></label><label class="rl-chipopt"><input type="radio" name="ac-weeks" value="2"><span>2 weeks</span></label><label class="rl-chipopt"><input type="radio" name="ac-weeks" value="4"><span>4 weeks</span></label></div></fieldset>
  <p class="rl-sheet__note" data-a="freezetext">Check-in is paused from today until 12 Oct. The plan will now end on 12 Oct 2026.</p>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-a-save="freeze">Freeze Membership</button></div>
</div>
<div class="rl-sheet" id="ac-unfreeze" data-modal role="alertdialog
<!-- …trimmed -->
```
