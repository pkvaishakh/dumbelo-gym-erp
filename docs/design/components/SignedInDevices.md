# SignedInDevices

Every device signed in to the person's account.

A detail screen behind Account Details. This device first, marked "This phone". Then every other device with where and when it was last used, each with its own Sign Out. Under the list: Sign Out All Other Devices, a `danger` outline button, and Change Password for anyone who sees a device they don't recognise.

- This phone cannot be signed out here. Sign Out on Account Details does that.
- Signing out asks first (SignedInDevicesConfirm). The row then leaves the list, and Account Details says "This phone only".
- Related: SignedInDevicesConfirm, SignedInDevicesNone.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-sscreen="devices">
<header class="rl-appbar rl-appbar--scroll"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <div class="rl-appbar__who"><h1 class="rl-pagetitle">Signed-in Devices</h1><p class="rl-appbar__branch">Meera Nair</p></div>
</div></header>
<main class="rl-app__main">
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">This device</h2></div><ul class="rl-card rl-results"><li><div class="rl-result" data-device="d1"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-result__text"><span class="rl-row__title">iPhone 15, Dumbelo app</span><span class="rl-row__meta">Bengaluru • Active now</span></span><span class="rl-tag rl-tag--now">This phone</span></div></li></ul></section>
<section class="rl-section" data-others><div class="rl-section__head"><h2 class="rl-section__title">Other devices</h2></div><ul class="rl-card rl-results"><li><div class="rl-result" data-device="d2"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-result__text"><span class="rl-row__title">Chrome on Windows</span><span class="rl-row__meta">Bengaluru • Today, 9:12 AM</span></span><button class="rl-button rl-button--secondary rl-button--sm" type="button" data-device-out="d2" aria-haspopup="dialog">Sign Out</button></div></li></ul><p class="rl-card rl-card--pad rl-row__meta" data-none hidden style="margin:0">No other device is signed in to your account.</p></section>
<section class="rl-section"><button class="rl-button rl-button--danger-quiet rl-button--block" type="button" data-device-out="all" aria-haspopup="dialog">Sign Out All Other Devices</button>
<p class="rl-row__meta" style="margin:var(--space-4) 0 var(--space-3)">Don’t recognise a device? Sign it out, then change your password.</p><button class="rl-button rl-button--secondary rl-button--block" type="button" data-account-password>Change Password</button></section>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Attendance</a><button class="rl-fab" type="button" data-sheet="dv-create" aria-haspopup="dialog" aria-expanded="false" aria-label="Create"><Icon class="rl-icon"/></button><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Reports</a><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>
<div class="rl-sheet" id="dv-create" role="dialog" aria-modal="true" aria-labelledby="dv-create-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="dv-create-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <p class="rl-sheet__label" id="dv-create-g1" style="margin-top:var(--space-1)">Members</p>
  <ul class="rl-sheet__list" aria-labelledby="dv-create-g1"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Member</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">New Subscription</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Collect Payment</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Mark Attendance</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Follow-up</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Book Session</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
  <p class="rl-sheet__label" id="dv-create-g2">Staff and expenses</p>
  <ul class="rl-sheet__list" aria-labelledby="dv-create-g2"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Trainer</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Receptionist</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Expense</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<div class="rl-sheet" id="dv-confirm" data-modal role="alertdialog" aria-modal="true" aria-labelledby="dv-confirm-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark rl-confirm__mark--blocked" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="dv-confirm-title" data-f="title">Sign out Chrome on Windows?</h2><p class="rl-confirm__text" data-f="text">It will need your password to sign in again. Anything open there is closed.</p></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--danger rl-button--block" type="button" data-device-confirm>Sign Out</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-keep>Cancel</button></div>
</div>
</div>
```
