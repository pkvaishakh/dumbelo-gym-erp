# MealList

The day's meals, each with a tick to mark it eaten.

Use on the Diet tab, in a `rl-card rl-meals` list. You provide each meal's name, time, what is in it and its calories, and save the tick. The round tick on the left is a checkbox with a 44px target. The first meal not yet eaten carries a "Next" tag.

- An eaten meal keeps its place; only its description goes to `ink-muted`.
- Put `data-kcal`, `data-p`, `data-c` and `data-f` on each meal so the NutritionSummary can add them up.

```html
<ul class="rl-card rl-meals">
  <li class="rl-meal is-next" data-kcal="200" data-p="5" data-c="24" data-f="10">
    <label class="rl-meal__check"><input type="checkbox" aria-label="Pre-workout snack eaten"><span><!-- check icon --></span></label>
    <div class="rl-meal__text">
      <p class="rl-meal__head"><span class="rl-row__title">Pre-workout snack</span><span class="rl-tag rl-tag--next">Next</span></p>
      <p class="rl-row__meta">10:15 AM</p><p class="rl-row__body">An apple and a handful of almonds</p>
    </div>
    <p class="rl-meal__kcal">200<small>kcal</small></p>
  </li>
</ul>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><ul class="rl-card rl-meals"><li class="rl-meal is-eaten" data-kcal="520" data-p="32" data-c="62" data-f="16"><label class="rl-meal__check"><input type="checkbox" aria-label="Breakfast eaten" checked><span><Icon class="rl-icon rl-icon--xs"/></span></label><div class="rl-meal__text"><p class="rl-meal__head"><span class="rl-row__title">Breakfast</span><span class="rl-tag rl-tag--next">Next</span></p><p class="rl-row__meta">8:00 AM</p><p class="rl-row__body">Oats with milk and a banana, 3 egg whites</p></div><p class="rl-meal__kcal">520<small>kcal</small></p></li><li class="rl-meal is-next" data-kcal="200" data-p="5" data-c="24" data-f="10"><label class="rl-meal__check"><input type="checkbox" aria-label="Pre-workout snack eaten"><span><Icon class="rl-icon rl-icon--xs"/></span></label><div class="rl-meal__text"><p class="rl-meal__head"><span class="rl-row__title">Pre-workout snack</span><span class="rl-tag rl-tag--next">Next</span></p><p class="rl-row__meta">10:15 AM</p><p class="rl-row__body">An apple and a handful of almonds</p></div><p class="rl-meal__kcal">200<small>kcal</small></p></li><li class="rl-meal" data-kcal="680" data-p="48" data-c="74" data-f="20"><label class="rl-meal__check"><input type="checkbox" aria-label="Lunch eaten"><span><Icon class="rl-icon rl-icon--xs"/></span></label><div class="rl-meal__text"><p class="rl-meal__head"><span class="rl-row__title">Lunch</span><span class="rl-tag rl-tag--next">Next</span></p><p class="rl-row__meta">1:30 PM</p><p class="rl-row__body">2 rotis, grilled chicken or paneer, dal, salad</p></div><p class="rl-meal__kcal">680<small>kcal</small></p></li></ul></div>
```
