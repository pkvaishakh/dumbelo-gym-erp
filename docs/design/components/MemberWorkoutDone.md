# MemberWorkoutDone

Today's plan and today's progress after the workout is finished.

The workout card keeps its place and its `ink` fill, and swaps the Start Workout button for a "Completed" line with a `volt` check and a "View Summary" button outlined in `on-ink`. In today's progress the workout ring is full, shows a check, and reads "Done, 45 min". The diet card and the other three progress items do not change.

## Markup (from the design system preview)

```html
<div class="rl-root demo" id="done-frame"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Today’s plan</h2></div><div class="rl-plan">
  <article class="rl-plan__card rl-plan__card--workout">
    <p class="rl-plan__kicker">Today’s workout</p>
    <div class="rl-plan__art"><div class="rl-barbell rl-barbell--on-ink rl-barbell--bleed" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
    <h3 class="rl-plan__title">Chest &amp; Triceps</h3>
    <p class="rl-plan__done"><span><Icon class="rl-icon rl-icon--xs"/></span>Completed</p>
    <p class="rl-plan__meta"><span class="rl-pill rl-pill--on-ink">6 of 6 exercises</span><span class="rl-pill rl-pill--on-ink">45 min</span></p>
    <span class="rl-plan__spacer"></span>
    <button class="rl-button rl-button--on-ink rl-button--block" type="button">View Summary</button>
  </article>
  <article class="rl-plan__card">
    <p class="rl-plan__kicker">Today’s diet</p>
    <span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span>
    <p class="rl-figure">2,350 <small>kcal</small></p>
    <p class="rl-plan__meta"><span class="rl-pill">Today’s target</span><span class="rl-pill">5 meals</span></p>
    <span class="rl-plan__spacer"></span>
    <a class="rl-button rl-button--secondary rl-button--block" href="#">View Diet</a>
  </article>
</div></section><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Today’s progress</h2></div><div class="rl-card rl-progress"><div class="rl-progress__item"><span class="rl-ring" style="--v:1.000"><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Workout</span><span class="rl-progress__value">Done, 45 min</span></span></div><div class="rl-progress__item"><span class="rl-ring" style="--v:0.221"><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Calories eaten</span><span class="rl-progress__value">520 / 2,350 kcal</span></span></div><div class="rl-progress__item"><span class="rl-ring" style="--v:0.250" data-water-v><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Water</span><span class="rl-progress__value" data-water-text>0.75 / 3 L</span></span><button class="rl-progress__add" type="button" data-sheet="rl-sheet-water" aria-haspopup="dialog" aria-label="Log water"><Icon class="rl-icon rl-icon--sm"/></button></div><div class="rl-progress__item"><span class="rl-ring" style="--v:0.355"><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Steps</span><span class="rl-progress__value">2,840 / 8,000</span></span></div></div></section></div>
```
