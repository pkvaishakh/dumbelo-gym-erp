# ExerciseEntry

One exercise being written down: its name, then sets, reps and weight side by side.

Use in a form that records a workout, in a `rl-entries` list. You provide the exercise and read the three numbers. An exercise from the plan shows its name as text; one the trainer adds shows a name field in its place. The bin on the right removes it.

- The three number fields are 48px tall with a small label above each, and use the numeric keyboard.
- Weight may be empty, with the placeholder "None", for a bodyweight exercise.
- A problem is stated under the fields of that exercise, with the field at fault ringed in `danger`.

```html
<ol class="rl-entries">
  <li class="rl-card rl-entry">
    <div class="rl-entry__head"><span class="rl-row__title">Bench Press</span><button class="rl-iconbtn rl-iconbtn--plain" type="button" aria-label="Remove Bench Press"><!-- trash icon --></button></div>
    <div class="rl-minis">
      <label class="rl-mini"><span>Sets</span><input type="number" inputmode="numeric" min="1" value="4"></label>
      <label class="rl-mini"><span>Reps</span><input type="number" inputmode="numeric" min="1" value="8"></label>
      <label class="rl-mini"><span>Weight, kg</span><input type="number" inputmode="decimal" step="0.5" placeholder="None" value="50"></label>
    </div>
  </li>
</ol>
```

## Markup (from the design system preview)

```html
<div class="rl-root rl-app demo" style="min-height:0;padding-bottom:0;background:none"><ol class="rl-entries"><li class="rl-card rl-entry"><div class="rl-entry__head"><span class="rl-row__title" data-entry-name>Bench Press</span><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-entry-remove aria-label="Remove Bench Press"><Icon class="rl-icon rl-icon--sm"/></button></div><div class="rl-minis"><label class="rl-mini"><span>Sets</span><input type="number" inputmode="numeric" min="1" data-k="sets" value="4" aria-label="Bench Press, sets"></label><label class="rl-mini"><span>Reps</span><input type="number" inputmode="numeric" min="1" data-k="reps" value="8" aria-label="Bench Press, reps"></label><label class="rl-mini"><span>Weight, kg</span><input type="number" inputmode="decimal" step="0.5" min="0" placeholder="None" data-k="kg" value="50" aria-label="Bench Press, weight, kg"></label></div><p class="rl-field__error" role="alert" hidden><Icon/><span></span></p></li><li class="rl-card rl-entry"><div class="rl-entry__head"><input class="rl-entry__name" type="text" autocomplete="off" placeholder="Exercise name" aria-label="Exercise name" data-entry-name><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-entry-remove aria-label="Remove exercise"><Icon class="rl-icon rl-icon--sm"/></button></div><div class="rl-minis"><label class="rl-mini"><span>Sets</span><input type="number" inputmode="numeric" min="1" data-k="sets" value="3" aria-label="sets"></label><label class="rl-mini"><span>Reps</span><input type="number" inputmode="numeric" min="1" data-k="reps" value="10" aria-label="reps"></label><label class="rl-mini"><span>Weight, kg</span><input type="number" inputmode="decimal" step="0.5" min="0" placeholder="None" data-k="kg" value="" aria-label="weight, kg"></label></div><p class="rl-field__error" role="alert" hidden><Icon/><span></span></p></li></ol></div>
```
