# NotificationsAllRead

After Mark All as Read: no dots, the subtitle says "All read", and the bell on the home screen has no badge.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-nscreen="member">
<header class="rl-appbar rl-appbar--scroll"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <div class="rl-appbar__who"><h1 class="rl-pagetitle">Notifications</h1><p class="rl-appbar__branch" data-unread-text>All read</p></div>
</div></header>
<main class="rl-app__main">
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Today</h2><button class="rl-link" type="button" data-read-all hidden><span>Mark All as Read</span></button></div><ul class="rl-card rl-activity"><li><button class="rl-activity__row rl-notice" type="button" data-notice="0" data-go="mworkout"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-activity__text"><span class="rl-row__body"><strong>Arjun</strong> updated your workout plan.</span><span class="rl-row__meta">1 h ago</span></span><span class="rl-notice__dot" aria-label="Unread" hidden></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></button></li><li><button class="rl-activity__row rl-notice" type="button" data-notice="1" data-go="mprogress"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-activity__text"><span class="rl-row__body">Record your weekly measurements.</span><span class="rl-row__meta">2 h ago</span></span><span class="rl-notice__dot" aria-label="Unread" hidden></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></button></li></ul></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Earlier</h2></div><ul class="rl-card rl-activity"><li><button class="rl-activity__row rl-notice" type="button" data-notice="2" data-go="mdiet"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-activity__text"><span class="rl-row__body">Your diet plan for next week is ready.</span><span class="rl-row__meta">Yesterday</span></span><span class="rl-notice__dot" aria-label="Unread" hidden></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></button></li><li><button class="rl-activity__row rl-notice" type="button" data-notice="3"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-activity__text"><span class="rl-row__body">Your Premium membership ends on <strong>28 Oct</strong>. Renew at the front desk.</span><span class="rl-row__meta">Thu 1 Oct</span></span><span class="rl-notice__dot" aria-label="Unread" hidden></span><span class="rl-notice__pad" aria-hidden="true"></span></button></li></ul></section>
<p class="rl-row__meta" style="text-align:center">Notifications from the last 7 days.</p>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Workout</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Diet</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Progress</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>

</div>
```
