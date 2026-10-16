# MemberDiet

The member's Diet tab, at phone width and full scroll length.

Top to bottom: the title with the date, the NutritionSummary (calories eaten against the day's target, and the three macros), the water row, the MealList for the day, the trainer's note and next week's plan.

You provide the target, the meals and their calories and macros. The script in `preview.html` adds a meal to the day when it is ticked, moves the "Next" tag to the first meal not yet eaten, and opens the water sheet. Replace the demo data with the member's plan.

- The figures match Member Home: the same target, the same calories eaten, the same water.
- Ticking a meal is the only logging. There is no food search and no calorie entry here; the trainer sets the plan.
- Where a meal offers a choice, write both in the line: "grilled chicken or paneer".
- Related: MemberDietDone, MemberDietWide.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-mscreen="diet" data-kcal-goal="2350">
<header class="rl-appbar"><div class="rl-appbar__in">
  <div class="rl-appbar__who"><h1 class="rl-pagetitle">Diet</h1><p class="rl-appbar__branch">Sunday, 4 October</p></div>
</div></header>
<main class="rl-app__main">
<div class="rl-app__cols">
<div class="rl-app__col"><section class="rl-section" aria-label="Today’s calories"><div class="rl-card"><div class="rl-nutri"><span class="rl-ring rl-ring--lg" data-kcal-ring role="img" aria-label="520 of 2,350 kcal eaten" style="--v:0.221"><Icon class="rl-ring__svg"/><span class="rl-ring__center" aria-hidden="true"><strong data-kcal>520</strong><small>of 2,350 kcal</small></span></span><div class="rl-macros"><div class="rl-macro" data-macro="p" data-goal="150"><div class="rl-macro__top"><span>Protein</span><span data-macro-text>32 / 150 g</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.213"></span></span></div><div class="rl-macro" data-macro="c" data-goal="265"><div class="rl-macro__top"><span>Carbs</span><span data-macro-text>62 / 265 g</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.234"></span></span></div><div class="rl-macro" data-macro="f" data-goal="77"><div class="rl-macro__top"><span>Fat</span><span data-macro-text>16 / 77 g</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.208"></span></span></div></div></div><p class="rl-cardfoot" data-kcal-note role="status">1,830 kcal left for today</p></div></section>
<section class="rl-section" aria-label="Water"><div class="rl-card rl-waterrow"><span class="rl-ring" style="--v:0.250" data-water-v><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Water</span><span class="rl-progress__value" data-water-text>0.75 / 3 L</span></span><button class="rl-progress__add" type="button" data-sheet="dt-water" aria-haspopup="dialog" aria-label="Log water"><Icon class="rl-icon rl-icon--sm"/></button></div></section></div>
<div class="rl-app__col"><section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">Today’s meals</h2><p class="rl-section__aside" data-meals-text role="status">1 of 5 eaten</p></div><ul class="rl-card rl-meals"><li class="rl-meal is-eaten" data-kcal="520" data-p="32" data-c="62" data-f="16"><label class="rl-meal__check"><input type="checkbox" aria-label="Breakfast eaten" checked><span><Icon class="rl-icon rl-icon--xs"/></span></label><div class="rl-meal__text"><p class="rl-meal__head"><span class="rl-row__title">Breakfast</span><span class="rl-tag rl-tag--next">Next</span></p><p class="rl-row__meta">8:00 AM</p><p class="rl-row__body">Oats with milk and a banana, 3 egg whites</p></div><p class="rl-meal__kcal">520<small>kcal</small></p></li><li class="rl-meal is-next" data-kcal="200" data-p="5" data-c="24" data-f="10"><label class="rl-meal__check"><input type="checkbox" aria-label="Pre-workout snack eaten"><span><Icon class="rl-icon rl-icon--xs"/></span></label><div class="rl-meal__text"><p class="rl-meal__head"><span class="rl-row__title">Pre-workout snack</span><span class="rl-tag rl-tag--next">Next</span></p><p class="rl-row__meta">10:15 AM</p><p class="rl-row__body">An apple and a handful of almonds</p></div><p class="rl-meal__kcal">200<small>kcal</small></p></li><li class="rl-meal" data-kcal="680" data-p="48" data-c="74" data-f="20"><label class="rl-meal__check"><input type="checkbox" aria-label="Lunch eaten"><span><Icon class="rl-icon rl-icon--xs"/></span></label><div class="rl-meal__text"><p class="rl-meal__head"><span class="rl-row__title">Lunch</span><span class="rl-tag rl-tag--next">Next</span></p><p class="rl-row__meta">1:30 PM</p><p class="rl-row__body">2 rotis, grilled chicken or paneer, dal, salad</p></div><p class="rl-meal__kcal">680<small>kcal</small></p></li><li class="rl-meal" data-kcal="250" data-p="15" data-c="35" data-f="6"><label class="rl-meal__check"><input type="checkbox" aria-label="Evening snack eaten"><span><Icon class="rl-icon rl-icon--xs"/></span></label><div class="rl-meal__text"><p class="rl-meal__head"><span class="rl-row__title">Evening snack</span><span class="rl-tag rl-tag--next">Next</span></p><p class="rl-row__meta">5:00 PM</p><p class="rl-row__body">Sprouts chaat and a glass of buttermilk</p></div><p class="rl-meal__kcal">250<small>kcal</small></p></li><li class="rl-meal" data-kcal="700" data-p="50" data-c="70" data-f="25"><label class="rl-meal__check"><input type="checkbox" aria-label="Dinner eaten"><span><Icon class="rl-icon rl-icon--xs"/></span></label><div class="rl-meal__text"><p class="rl-meal__head"><span class="rl-row__title">Dinner</span><span class="rl-tag rl-tag--next">Next</span></p><p class="rl-row__meta">8:30 PM</p><p class="rl-row__body">Brown rice, grilled fish or tofu, sautéed vegetables</p></div><p class="rl-meal__kcal">700<small>kcal</small></p></li></ul></section>
<section class="rl-section"><div class="rl-section__head"><h2 class="rl-section__title">From Arjun</h2></div><ul class="rl-card rl-notes"><li><p class="rl-row__body">Have dinner before 9 PM, and drink a glass of water before each meal.</p><p class="rl-row__meta">Arjun Rao, 28 Sep</p></li></ul></section>
<section class="rl-section" aria-label="Next week"><ul class="rl-card rl-remind"><li><a class="rl-remind__row" href="#"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-remind__text"><span class="rl-row__body">Your diet plan for next week is ready</span><span class="rl-row__meta">Starts Mon 5 Oct</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li></ul></section></div>
</div>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Workout</a><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Diet</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Progress</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>
<div class="rl-sheet" id="dt-water" role="dialog" aria-modal="true" aria-labelledby="dt-water-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="dt-water-title">Log water</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-water" data-water-total="0.75">
    <p class="rl-figure" data-water-text>0.75 / 3 L</p>
    <span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" data-water-v style="--v:0.250"></span></span>
    <p class="rl-row__meta">Tap an amount each time you drink. It adds to today’s total.</p>
    <div class="rl-water__adds"><button class="rl-button rl-button--secondary" type="button" data-add="0.25">+250 ml</button><button class="rl-button rl-button--secondary" type="button" data-add="0.5">+500 ml</button><button class="rl-button rl-button--secondary" type="button" data-add="0.75">+750 ml</button></div>
    <button class="rl-button rl-button--block" type="button" data-close>Done</button>
  </div>
</div>
</div>
```
