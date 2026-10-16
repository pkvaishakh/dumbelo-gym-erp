# CheckInSheet

The sheet that answers a check-in: confirmed, or blocked.

Built on Sheet. You provide the member (photo or initials, name, ID, status, plan, date) and the time. Both forms share the layout: a 56px round mark, a title, an optional line of text, the member's card (`rl-idcard` with an `rl-facts` list), then full-width buttons.

- Confirmed: `volt` mark with a check, title "Checked in at 8:41 AM", facts "Plan" and "Valid until", buttons "Done" and "View Profile".
- Blocked: `rl-confirm__mark--blocked` with the ban icon, title "Check-in blocked", one sentence with the reason and the fix, facts "Plan" and "Expired on", buttons "Renew" and "Collect Payment".
- Never use colour alone to tell the two apart: the icon and the title differ too.
- Receptionist Home and Attendance both use it. To look at a check-in that already happened, use VisitSheet.

## Markup (from the design system preview)

```html
<div class="rl-root"><div class="rl-scrim is-open" data-close></div>
<div class="rl-sheet" id="rl-sheet-create" role="dialog" aria-modal="true" aria-labelledby="rl-sheet-create-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="rl-sheet-create-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button" data-search-open><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Check In</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Member</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Collect Payment</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Subscription</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<div class="rl-sheet is-open" id="rl-sheet-ok" role="dialog" aria-modal="true" aria-labelledby="rl-sheet-ok-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="rl-sheet-ok-title">Checked in at 8:41 AM</h2><p class="rl-confirm__text" data-f="note" hidden></p></div>
  <div class="rl-idcard">
    <div class="rl-idcard__who"><span class="rl-photo rl-photo--lg" aria-hidden="true" data-f="initials">RK</span><span><span class="rl-row__title" data-f="name">Rahul Kumar</span><span class="rl-row__meta" data-f="id">RL-2041</span><span class="rl-status rl-status--active" data-f="status">Active</span></span></div>
    <dl class="rl-facts"><dt>Plan</dt><dd data-f="plan">Premium, with personal training</dd><dt>Valid until</dt><dd data-f="date">28 Oct 2026</dd></dl>
  </div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-done>Done</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-done>View Profile</button></div>
</div>
<div class="rl-sheet" id="rl-sheet-blocked" role="dialog" aria-modal="true" aria-labelledby="rl-sheet-blocked-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head" style="justify-content:flex-end;margin-bottom:calc(var(--space-8) * -1)"><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-confirm"><span class="rl-confirm__mark rl-confirm__mark--blocked" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="rl-sheet-blocked-title">Check-in blocked</h2><p class="rl-confirm__text">This membership has expired. Renew it to check the member in.</p></div>
  <div class="rl-idcard">
    <div class="rl-idcard__who"><span class="rl-photo rl-photo--lg" aria-hidden="true" data-f="initials">RM</span><span><span class="rl-row__title" data-f="name">Raghav Menon</span><span class="rl-row__meta" data-f="id">RL-1532</span><span class="rl-status rl-status--expired" data-f="status">Expired</span></span></div>
    <dl class="rl-facts"><dt>Plan</dt><dd data-f="plan">Monthly</dd><dt>Expired on</dt><dd data-f="date">28 Sep 2026</dd></dl>
  </div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button">Renew</button><button class="rl-button rl-button--secondary rl-button--block" type="button">Collect Payment</button></div>
</div>
<div class="rl-sheet" id="rl-sheet-scan" role="dialog" aria-modal="true" aria-labelledby="rl-sheet-scan-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="rl-sheet-scan-title">Scan member QR</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div style="display:grid;place-items:center;aspect-ratio:4/3;margin-top:var(--space-2);border-radius:var(--radius-md);background:var(--ink);color:var(--on-ink)"><span style="display:grid;justify-items:center;gap:var(--space-2);font-size:14px;line-height:20px"><Icon class="rl-icon"/><span>Camera preview</span></span></div>
  <p class="rl-confirm__text" style="margin-top:var(--space-3);text-align:center">Hold the member’s QR code inside the frame.</p>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--secondary rl-button--block" type="button" data-search-open>Search Instead</button></div>
</div></div>
```
