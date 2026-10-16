# SetTracker

One exercise during a workout, with a chip to tick for each set.

Use in a workout in progress. You provide the exercise and its sets and save each tick. Each chip is a checkbox 56px tall: "Set 1" over the reps before it is done, a tick over the reps on a `volt` fill after. Four chips fit a row; a fifth wraps.

- When every set is ticked, add `is-done` to the exercise row so its number becomes a tick.
- The whole chip is the target. Tapping again unticks it.
- In the trainer's LiveSession the load is a button (`button.rl-ex__load` with a pencil icon) that opens the Change load sheet.

```html
<li class="rl-card rl-track">
  <div class="rl-ex"><!-- as in ExerciseList --></div>
  <div class="rl-sets">
    <label class="rl-set"><input type="checkbox" aria-label="Bench Press, set 1"><span><!-- check icon --><b>Set 1</b><small>8 reps</small></span></label>
  </div>
</li>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><ol style="margin:0;padding:0;list-style:none;display:grid;gap:var(--space-4)"><li class="rl-card rl-track"><div class="rl-ex is-done"><span class="rl-ex__num"><span>1</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Bench Press</span><span class="rl-row__meta">4 sets × 8 reps</span></span><span class="rl-ex__load">50 kg</span></div><div class="rl-sets"><label class="rl-set"><input type="checkbox" aria-label="Bench Press, set 1" checked><span><Icon class="rl-icon"/><b>Set 1</b><small>8 reps</small></span></label><label class="rl-set"><input type="checkbox" aria-label="Bench Press, set 2" checked><span><Icon class="rl-icon"/><b>Set 2</b><small>8 reps</small></span></label><label class="rl-set"><input type="checkbox" aria-label="Bench Press, set 3" checked><span><Icon class="rl-icon"/><b>Set 3</b><small>8 reps</small></span></label><label class="rl-set"><input type="checkbox" aria-label="Bench Press, set 4" checked><span><Icon class="rl-icon"/><b>Set 4</b><small>8 reps</small></span></label></div></li><li class="rl-card rl-track"><div class="rl-ex"><span class="rl-ex__num"><span>3</span><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-ex__text"><span class="rl-row__title">Cable Fly</span><span class="rl-row__meta">3 sets × 12 reps</span></span><span class="rl-ex__load">15 kg</span></div><div class="rl-sets"><label class="rl-set"><input type="checkbox" aria-label="Cable Fly, set 1" checked><span><Icon class="rl-icon"/><b>Set 1</b><small>12 reps</small></span></label><label class="rl-set"><input type="checkbox" aria-label="Cable Fly, set 2"><span><Icon class="rl-icon"/><b>Set 2</b><small>12 reps</small></span></label><label class="rl-set"><input type="checkbox" aria-label="Cable Fly, set 3"><span><Icon class="rl-icon"/><b>Set 3</b><small>12 reps</small></span></label></div></li></ol></div>
```
