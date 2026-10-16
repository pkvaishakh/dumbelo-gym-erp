# NextSession

The hero card of Trainer Home: who the trainer is about to train, and the one button that starts it.

It is the strongest element on the screen: an `ink` card with a `volt` countdown chip and a `volt` primary button. You provide the countdown, the time, the session type and length, the member (photo or initials, name, goal, current weight), today's workout, whether the member has checked in, and the two actions.

- Next: chip "Starts in 25 min", the time as a `figure`, the member row with outlined pills ("Fat Loss", "71.2 kg"), the workout as a `title`, a check-in line, then "Start Session" (`rl-button--accent`) and "View Member" (`rl-button--on-ink`).
- In progress: chip "Started 11:00 AM", the elapsed minutes as the `figure` with a bar against the length, then "End Session" and "Open Session", which returns to the LiveSession screen.
- Empty: when nothing is left today, a plain `ground` card (`rl-hero--empty`) saying so, naming the next session, with a small "View Schedule" button.
- Under an hour the countdown is minutes only; over an hour, hours and minutes ("Starts in 1 h 45 min").
- Show only one session here. The rest of the day belongs in the schedule.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><article class="rl-hero" aria-label="Next session">
  <div class="rl-hero__top"><p class="rl-hero__kicker">Next session</p><span class="rl-pill rl-pill--volt"><Icon class="rl-icon rl-icon--xs"/>Starts in 25 min</span></div>
  <p class="rl-figure">11:00 AM <small>Personal Training, 45 min</small></p>
  <div class="rl-hero__member"><span class="rl-photo rl-photo--lg" aria-hidden="true">RK</span><span><span class="rl-hero__name">Rahul Kumar</span><span class="rl-hero__tags"><span class="rl-pill rl-pill--on-ink">Fat Loss</span><span class="rl-pill rl-pill--on-ink">71.2 kg</span></span></span></div>
  <div><p class="rl-hero__kicker">Today’s workout</p><p class="rl-hero__title">Chest &amp; Triceps</p></div>
  <p class="rl-hero__note"><Icon class="rl-icon rl-icon--xs"/>Not checked in yet</p>
  <div class="rl-hero__actions"><button class="rl-button rl-button--accent" type="button" data-session="live">Start Session</button><a class="rl-button rl-button--on-ink" href="#">View Member</a></div>
</article><article class="rl-hero" aria-label="Session in progress">
  <div class="rl-hero__top"><p class="rl-hero__kicker">Session in progress</p><span class="rl-pill rl-pill--volt"><Icon class="rl-icon rl-icon--xs"/>Started 11:00 AM</span></div>
  <p class="rl-figure">12 min <small>of 45 min</small></p>
  <span class="rl-bar" role="img" aria-label="12 of 45 minutes"><span class="rl-bar__fill" style="--v:0.267"></span></span>
  <div class="rl-hero__member"><span class="rl-photo rl-photo--lg" aria-hidden="true">RK</span><span><span class="rl-hero__name">Rahul Kumar</span><span class="rl-hero__tags"><span class="rl-pill rl-pill--on-ink">Fat Loss</span><span class="rl-pill rl-pill--on-ink">71.2 kg</span></span></span></div>
  <div><p class="rl-hero__kicker">Today’s workout</p><p class="rl-hero__title">Chest &amp; Triceps</p></div>
  <div class="rl-hero__actions"><button class="rl-button rl-button--accent" type="button" data-session="next">End Session</button><a class="rl-button rl-button--on-ink" href="#" data-open-session>Open Session</a></div>
</article><article class="rl-hero rl-hero--empty" aria-label="Next session">
  <span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span>
  <div><p class="rl-row__title">No more sessions today</p><p class="rl-row__meta">Your next one is tomorrow at 7:00 AM with Meenal Shah.</p></div>
  <a class="rl-button rl-button--secondary rl-button--sm" href="#">View Schedule</a>
</article></div>
```
