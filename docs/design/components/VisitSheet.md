# VisitSheet

The sheet for one check-in: the member, when they checked in, and what can be done about it.

Built on Sheet. You provide the member (photo or initials, name, ID, status) and the visit. Top to bottom: the title ("Today’s visit" or "Visit on Sun 4 Oct"), the member's card with their StatusBadge, a DetailList of two rows, then full-width buttons.

- The rows are "Checked in" with the time and "Last 7 days" with how many check-ins the member made in the week. A check-in is only a member and a time, so there is no check-out, no visit length and no method.
- Buttons, in this order: View Profile (secondary), Remove Check-In (`rl-button--danger-quiet`, today only).
- Remove Check-In never removes at once. It opens the confirmation shown in AttendanceRemove.
- For an earlier day the sheet has View Profile only.

## Markup (from the design system preview)

```html
<div class="rl-root"><div class="rl-scrim is-open" data-close></div>
<div class="rl-sheet" id="at-create" role="dialog" aria-modal="true" aria-labelledby="at-create-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="at-create-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button" data-search-open><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Check In</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Member</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Collect Payment</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Subscription</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<div class="rl-sheet is-open" id="at-visit" role="dialog" aria-modal="true" aria-labelledby="at-visit-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="at-visit-title" data-f="title">Today’s visit</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-idcard"><div class="rl-idcard__who"><span class="rl-photo rl-photo--lg" aria-hidden="true" data-f="initials">SK</span><span><span class="rl-row__title" data-f="name">Sana Kapoor</span><span class="rl-row__meta" data-f="id">RL-2210</span><span class="rl-status rl-status--active" data-f="status">Active</span></span></div></div>
  <dl class="rl-details"><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Checked in</dt><dd data-f="in">8:38 AM</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Last 7 days</dt><dd data-f="week">2 visits</dd></div></dl>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--secondary rl-button--block" type="button" data-visit-profile>View Profile</button><button class="rl-button rl-button--danger-quiet rl-button--block" type="button" data-visit-remove-open aria-haspopup="dialog">Remove Check-In</button></div>
</div>
<div class="rl-sheet" id="at-confirm" data-modal role="alertdialog" aria-modal="true" aria-labelledby="at-confirm-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark rl-confirm__mark--blocked" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="at-confirm-title">Remove this check-in?</h2><p class="rl-confirm__text" data-f="deltext">Sana Kapoor, 8:38 AM today. Use this when the wrong member was checked in. This cannot be undone.</p></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--danger rl-button--block" type="button" data-visit-remove>Remove Check-In</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-keep>Keep It</button></div>
</div>
<div class="rl-sheet" id="at-ok" role="dialog" aria-modal="true" aria-labelledby="at-ok-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="at-ok-title">Checked in at 8:41 AM</h2><p class="rl-confirm__text" data-f="note" hidden></p></div>
  <div class="rl-idcard">
    <div class="rl-idcard__who"><span class="rl-photo rl-photo--lg" aria-hidden="true" data-f="initials">RK</span><span><span class="rl-row__title" data-f="name">Rahul Kumar</span><span class="rl-row__meta" data-f="id">RL-2041</span><span class="rl-status rl-status--active" data-f="status">Active</span></span></div>
    <dl class="rl-facts"><dt>Plan</dt><dd data-f="plan">Premium, with personal training</dd><dt>Valid until</dt><dd data-f="date">28 Oct 2026</dd></dl>
  </div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-done>Done</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-ok-profile>View Profile</button></div>
</div>
<div class="rl-sheet" id="at-blocked" role="dialog" aria-modal="true" aria-labelledby="at-blocked-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head" style="justify-content:flex-end;margin-bottom:calc(var(--space-8) * -1)"><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-confirm"><span class="rl-confirm__mark rl-confirm__mark--blocked" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="at-blocked-title">Check-in blocked</h2><p class="rl-confirm__text">This membership has expired. Renew it to check the member in.</p></div>
  <div class="rl-idcard">
    <div class="rl-idcard__who"><span class="rl-photo rl-photo--lg" aria-hidden="true" data-f="initials">RM</span><span><span class="rl-row__title" data-f="name">Raghav Menon</span><span class="rl-row__meta" data-f="id">RL-1532</span><span class="rl-status rl-status--expired" data-f="status">Expired</span></span></div>
    <dl class="rl-facts"><dt>Plan</dt><dd data-f="plan">Monthly</dd><dt>Expired on</dt><dd data-f="date">28 Sep 2026</dd></dl>
  </div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button">Renew</button><button class="rl-button rl-button--secondary rl-button--block" type="button">Collect Payment</button></div>
</div></div>
```
