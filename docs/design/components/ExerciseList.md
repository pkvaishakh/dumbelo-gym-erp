# ExerciseList

The exercises of a workout as a numbered list: name, sets and reps, and the load.

Use on the Workout tab, in a `rl-card rl-exlist` list. You provide the exercises in order. Rows are not links. A done exercise swaps its number for a tick on `volt`: add `is-done` to the row, or to the list when the whole workout is finished.

- Write sets and reps as "4 sets × 8 reps". Write the load as the member would say it: "50 kg", "16 kg each", "Bodyweight".

```html
<ul class="rl-card rl-exlist">
  <li><div class="rl-ex">
    <span class="rl-ex__num"><span>1</span><!-- check icon --></span>
    <span class="rl-ex__text"><span class="rl-row__title">Bench Press</span><span class="rl-row__meta">4 sets × 8 reps</span></span>
    <span class="rl-ex__load">50 kg</span>
  </div></li>
</ul>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><ul class="rl-card rl-exlist"><li><div class="rl-ex is-done"><span class="rl-ex__num"><span>1</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Bench Press</span><span class="rl-row__meta">4 sets × 8 reps</span></span><span class="rl-ex__load">50 kg</span></div></li><li><div class="rl-ex"><span class="rl-ex__num"><span>2</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Incline Dumbbell Press</span><span class="rl-row__meta">3 sets × 10 reps</span></span><span class="rl-ex__load">16 kg each</span></div></li><li><div class="rl-ex"><span class="rl-ex__num"><span>3</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Cable Fly</span><span class="rl-row__meta">3 sets × 12 reps</span></span><span class="rl-ex__load">15 kg</span></div></li></ul></div>
```
