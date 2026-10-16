# NutritionSummary

The day's eating in one card: a large ring of calories eaten against the target, and a bar for each macro.

Use at the top of the Diet tab. You provide the target and what has been eaten. The ring's centre shows calories eaten over "of 2,350 kcal"; each macro row shows grams eaten and its target above a bar. The line under the card says what is left, or that the target is met.

- The ring and bars fill in `volt` and always sit beside their numbers.
- Use `rl-ring rl-ring--lg` for the ring. It is the only large ring in the app; elsewhere rings stay 44px.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-card"><div class="rl-nutri"><span class="rl-ring rl-ring--lg" data-kcal-ring role="img" aria-label="520 of 2,350 kcal eaten" style="--v:0.221"><Icon class="rl-ring__svg"/><span class="rl-ring__center" aria-hidden="true"><strong data-kcal>520</strong><small>of 2,350 kcal</small></span></span><div class="rl-macros"><div class="rl-macro" data-macro="p" data-goal="150"><div class="rl-macro__top"><span>Protein</span><span data-macro-text>32 / 150 g</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.213"></span></span></div><div class="rl-macro" data-macro="c" data-goal="265"><div class="rl-macro__top"><span>Carbs</span><span data-macro-text>62 / 265 g</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.234"></span></span></div><div class="rl-macro" data-macro="f" data-goal="77"><div class="rl-macro__top"><span>Fat</span><span data-macro-text>16 / 77 g</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.208"></span></span></div></div></div><p class="rl-cardfoot" data-kcal-note role="status">1,830 kcal left for today</p></div></div>
```
