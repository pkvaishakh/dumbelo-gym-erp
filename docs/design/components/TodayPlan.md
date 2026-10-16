# TodayPlan

The two things to do today, side by side: the workout and the diet.

The workout card is the loudest element on Member Home: `ink` fill, the barbell in its `on-ink` form, the workout's name as a `title`, two outlined pills (exercises, duration) and the one `volt` button on the screen, "Start Workout". The diet card is a plain `ground` card: the calorie target as a `figure`, two pills, and a secondary "View Diet" button.

You provide the workout name, the counts, the calorie target and the two actions. The cards sit in two columns from 380px and stack below that, workout first.

- Completed state: replace the pills row with `rl-plan__done` ("Completed" with a `volt` check) plus the pills, and the button with "View Summary" (`rl-button--on-ink`).
- One photo may replace the barbell on the workout card. Nothing else on Member Home takes a photo.
- Keep both buttons on the same baseline: `rl-plan__spacer` pushes them to the bottom of the cards.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-plan">
  <article class="rl-plan__card rl-plan__card--workout">
    <p class="rl-plan__kicker">Today’s workout</p>
    <div class="rl-plan__art"><div class="rl-barbell rl-barbell--on-ink rl-barbell--bleed" aria-hidden="true"><span class="rl-barbell__tip"></span><span class="rl-plate rl-plate--sm"></span><span class="rl-plate rl-plate--md"></span><span class="rl-plate rl-plate--lg"></span><span class="rl-plate"></span><span class="rl-plate rl-plate--volt"></span><span class="rl-barbell__collar"></span><span class="rl-barbell__shaft"></span></div></div>
    <h3 class="rl-plan__title">Chest &amp; Triceps</h3>
    <p class="rl-plan__meta"><span class="rl-pill rl-pill--on-ink">6 exercises</span><span class="rl-pill rl-pill--on-ink">45 min</span></p>
    <span class="rl-plan__spacer"></span>
    <button class="rl-button rl-button--accent rl-button--block" type="button" data-start>Start Workout</button>
  </article>
  <article class="rl-plan__card">
    <p class="rl-plan__kicker">Today’s diet</p>
    <span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span>
    <p class="rl-figure">2,350 <small>kcal</small></p>
    <p class="rl-plan__meta"><span class="rl-pill">Today’s target</span><span class="rl-pill">5 meals</span></p>
    <span class="rl-plan__spacer"></span>
    <a class="rl-button rl-button--secondary rl-button--block" href="#">View Diet</a>
  </article>
</div></div>
```
