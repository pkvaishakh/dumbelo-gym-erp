# WorkoutWeek

The week's workouts at a glance: how many are done, and a dot for each day.

Use on the Workout tab. You provide the seven days and their state. A done day is a `volt` dot with a tick, a rest day is a `surface` dot with a dash, today is a ring until its workout is done. The line above says the count in words, with one line of encouragement under it.

- It counts workouts, not check-ins. The check-in streak lives on the StreakCard and the AttendanceCalendar.
- Give every dot an `aria-label` that names the workout or says "Rest day".

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-card rl-card--pad"><div><p class="rl-row__title">3 of 4 workouts done</p><p class="rl-row__meta">Finish today’s to complete the week.</p></div><ol class="rl-week" aria-label="This week"><li><span class="rl-week__dot" aria-label="Legs, done"><Icon class="rl-icon rl-icon--xs"/></span>Mon</li><li><span class="rl-week__dot" aria-label="Shoulders &amp; Core, done"><Icon class="rl-icon rl-icon--xs"/></span>Tue</li><li><span class="rl-week__dot rl-week__dot--rest" aria-label="Rest day"><Icon class="rl-icon rl-icon--xs"/></span>Wed</li><li><span class="rl-week__dot" aria-label="Back &amp; Biceps, done"><Icon class="rl-icon rl-icon--xs"/></span>Thu</li><li><span class="rl-week__dot rl-week__dot--rest" aria-label="Rest day"><Icon class="rl-icon rl-icon--xs"/></span>Fri</li><li><span class="rl-week__dot rl-week__dot--rest" aria-label="Rest day"><Icon class="rl-icon rl-icon--xs"/></span>Sat</li><li class="is-today"><span class="rl-week__dot" aria-label="Chest &amp; Triceps, not done yet"></span>Today</li></ol></div></div>
```
