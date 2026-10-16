# MemberWorkoutWide

The Workout tab from 768px.

Two columns: today's workout and its exercises on the left; the week, the trainer's note and what is coming up on the right. The bottom navigation stays.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-mscreen="workout">
<header class="rl-appbar"><div class="rl-appbar__in">
  <div class="rl-appbar__who"><h1 class="rl-pagetitle">Workout</h1><p class="rl-appbar__branch">Week 10 of 13 • Fat Loss plan</p></div>
</div></header>
<main class="rl-app__main">
<div class="rl-app__cols">
<div class="rl-app__col"><section class="rl-section" aria-label="Today’s workout"><div class="rl-hero" data-when="todo">
  <p class="rl-hero__kicker">Today’s workout</p>
  <div class="rl-plan__art"><div class="rl-barbell rl-barbell--on-ink rl-barbell--bleed" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
  <h2 class="rl-hero__title">Chest &amp; Triceps</h2>
  <div class="rl-hero__tags"><span class="rl-pill rl-pill--on-ink">6 exercises</span><span class="rl-pill rl-pill--on-ink">18 sets</span><span class="rl-pill rl-pill--on-ink">45 min</span></div>
  <p class="rl-hero__note"><Icon class="rl-icon rl-icon--xs"/>With Arjun at 11:00 AM</p>
  <button class="rl-button rl-button--accent rl-button--block" type="button" data-start>Start Workout</button>
</div>
<div class="rl-hero" data-when="done" hidden>
  <p class="rl-hero__kicker">Today’s workout</p>
  <div class="rl-plan__art"><div class="rl-barbell rl-barbell--on-ink rl-barbell--bleed" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
  <h2 class="rl-hero__title">Chest &amp; Triceps</h2>
  <p class="rl-plan__done"><span><Icon class="rl-icon rl-icon--xs"/></span>Completed</p>
  <div class="rl-hero__tags"><span class="rl-pill rl-pill--on-ink" data-done-ex>6 of 6 exercises</span><span class="rl-pill rl-pill--on-ink" data-done-min>45 min</span></div>
  <button class="rl-button rl-button--on-ink rl-button--block" type="button">View Summary</button>
</div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Exercises</h2><p class="rl-section__aside">18 sets</p></div><ul class="rl-card rl-exlist"><li><div class="rl-ex"><span class="rl-ex__num"><span>1</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Bench Press</span><span class="rl-row__meta">4 sets × 8 reps</span></span><span class="rl-ex__load">50 kg</span></div></li><li><div class="rl-ex"><span class="rl-ex__num"><span>2</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Incline Dumbbell Press</span><span class="rl-row__meta">3 sets × 10 reps</span></span><span class="rl-ex__load">16 kg each</span></div></li><li><div class="rl-ex"><span class="rl-ex__num"><span>3</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Cable Fly</span><span class="rl-row__meta">3 sets × 12 reps</span></span><span class="rl-ex__load">15 kg</span></div></li><li><div class="rl-ex"><span class="rl-ex__num"><span>4</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Triceps Pushdown</span><span class="rl-row__meta">3 sets × 12 reps</span></span><span class="rl-ex__load">25 kg</span></div></li><li><div class="rl-ex"><span class="rl-ex__num"><span>5</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Overhead Triceps Extension</span><span class="rl-row__meta">3 sets × 12 reps</span></span><span class="rl-ex__load">14 kg</span></div></li><li><div class="rl-ex"><span class="rl-ex__num"><span>6</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Push-ups</span><span class="rl-row__meta">2 sets × max reps</span></span><span class="rl-ex__load">Bodyweight</span></div></li></ul></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">This week</h2></div><div class="rl-card rl-card--pad"><div data-when="todo"><p class="rl-row__title">3 of 4 workouts done</p><p class="rl-row__meta">Finish today’s to complete the week.</p></div><div data-when="done" hidden><p class="rl-row__title">4 of 4 workouts done</p><p class="rl-row__meta">That’s the full week. Rest well tonight.</p></div><ol class="rl-week" aria-label="This week"><li><span class="rl-week__dot" aria-label="Legs, done"><Icon class="rl-icon rl-icon--xs"/></span>Mon</li><li><span class="rl-week__dot" aria-label="Shoulders &amp; Core, done"><Icon class="rl-icon rl-icon--xs"/></span>Tue</li><li><span class="rl-week__dot rl-week__dot--rest" aria-label="Rest day"><Icon class="rl-icon rl-icon--xs"/></span>Wed</li><li><span class="rl-week__dot" aria-label="Back &amp; Biceps, done"><Icon class="rl-icon rl-icon--xs"/></span>Thu</li><li><span class="rl-week__dot rl-week__dot--rest" aria-label="Rest day"><Icon class="rl-icon rl-icon--xs"/></span>Fri</li><li><span class="rl-week__dot rl-week__dot--rest" aria-label="Rest day"><Icon class="rl-icon rl-icon--xs"/></span>Sat</li><li class="is-today" data-when="todo"><span class="rl-week__dot" aria-label="Chest &amp; Triceps, not done yet"></span>Today</li><li class="is-today" data-when="done" hidden><span class="rl-week__dot" aria-label="Chest &amp; Triceps, done"><Icon class="rl-icon rl-icon--xs"/></span>Today</li></ol></div></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">From Arjun</h2></div><ul class="rl-card rl-notes"><li><p class="rl-row__body">Rest 90 seconds between bench sets. If the last set feels easy, add 2.5 kg next time.</p><p class="rl-row__meta">Arjun Rao, 1 h ago</p></li></ul></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Coming up</h2></div><ul class="rl-card rl-agenda"><li><div class="rl-agenda__row"><span class="rl-agenda__time">Mon<br>5 Oct</span><span><span class="rl-agenda__top"><span class="rl-tag">PT</span><span class="rl-row__title">Back &amp; Biceps</span></span><span class="rl-row__meta">9:00 AM with Arjun, 45 min</span></span></div></li><li><div class="rl-agenda__row"><span class="rl-agenda__time">Wed<br>7 Oct</span><span><span class="rl-agenda__top"><span class="rl-tag">Workout</span><span class="rl-row__title">Legs</span></span><span class="rl-row__meta">7 exercises, 50 min</span></span></div></li></ul></section></div>
</div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Workout</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Diet</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Progress</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>

</div>
```
