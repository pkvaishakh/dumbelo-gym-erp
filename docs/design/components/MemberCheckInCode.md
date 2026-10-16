# MemberCheckInCode

The member's check-in code, open as a sheet over More.

See CheckInCode. One action, Done. The same code works at the door scanner and at the front desk, where it ends up as "QR code at the door" or under the receptionist's name on that day's Attendance.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-morescreen="member">
<header class="rl-appbar"><div class="rl-appbar__in">
  <div class="rl-appbar__who"><h1 class="rl-pagetitle">More</h1><p class="rl-appbar__branch">Rahul Kumar • Member</p></div>
  <button class="rl-avatar rl-pressable" type="button" aria-label="Profile: Rahul Kumar">RK</button>
</div></header>
<main class="rl-app__main">
<div class="rl-app__cols"><div class="rl-app__col"><section class="rl-section" aria-label="Check in"><button class="rl-tile rl-tile--accent rl-pressable rl-codetile" type="button" data-sheet="mm-code" aria-haspopup="dialog"><Icon class="rl-icon"/><span class="rl-tile__text">Check-in Code<span class="rl-tile__hint">Show it at the door to check in</span></span><Icon class="rl-icon rl-icon--sm"/></button></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Membership</h2></div><div class="rl-card"><dl class="rl-details"><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Plan</dt><dd>Premium, with personal training</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Valid until</dt><dd>28 Oct 2026</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Trainer</dt><dd>Arjun Rao</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Member ID</dt><dd>RL-2041</dd></div></dl><p class="rl-cardfoot">To renew or change your plan, ask at the front desk.</p></div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Your gym</h2></div><div class="rl-card"><dl class="rl-details"><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Branch</dt><dd>Rackline Indiranagar</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Opening hours</dt><dd>6 AM to 10 PM, every day</dd></div></dl></div></section></div><div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Account</h2></div><ul class="rl-card rl-remind"><li><button class="rl-remind__row" type="button" data-go="account"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-remind__text"><span class="rl-row__title">Account Details</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></button></li><li><button class="rl-remind__row" type="button" data-sign-out><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-remind__text"><span class="rl-row__title">Sign Out</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></button></li></ul></section></div></div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Workout</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Diet</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Progress</a><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim is-open" data-close></div>
<div class="rl-sheet is-open" id="mm-code" role="dialog" aria-modal="true" aria-labelledby="mm-code-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="mm-code-title">Check-in code</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-checkcode"><Icon class="rl-qr"/><p class="rl-row__title">Rahul Kumar</p><p class="rl-row__meta">RL-2041 • Premium Plan</p></div>
  <p class="rl-confirm__text" style="text-align:center">Hold it up to the scanner at the door, or show it at the front desk.</p>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-close>Done</button></div>
</div>
</div>
```
