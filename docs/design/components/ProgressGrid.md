# ProgressGrid

Today's progress in one compact card: four equal items, each a ring with an icon and a value in words.

Use once on Member Home. You provide, for each item, a label, the value as text ("520 / 2,350 kcal") and the fraction done as `--v` on the ring (0 to 1). Items: Workout, Calories eaten, Water, Steps.

- The value is always written out. The ring supports it and never stands alone.
- A ring at zero uses `rl-ring--empty` (track only) and the value says so: "Not started".
- Water carries a 36px "+" button (44px tap area) that opens the quick-log sheet.
- Rings draw in once on load and animate when their value changes.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-card rl-progress"><div class="rl-progress__item"><span class="rl-ring rl-ring--empty" style="--v:0.000"><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Workout</span><span class="rl-progress__value">Not started</span></span></div><div class="rl-progress__item"><span class="rl-ring" style="--v:0.221"><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Calories eaten</span><span class="rl-progress__value">520 / 2,350 kcal</span></span></div><div class="rl-progress__item"><span class="rl-ring" style="--v:0.250" data-water-v><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Water</span><span class="rl-progress__value" data-water-text>0.75 / 3 L</span></span><button class="rl-progress__add" type="button" data-sheet="rl-sheet-water" aria-haspopup="dialog" aria-label="Log water"><Icon class="rl-icon rl-icon--sm"/></button></div><div class="rl-progress__item"><span class="rl-ring" style="--v:0.355"><Icon class="rl-ring__svg"/><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-progress__text"><span class="rl-progress__label">Steps</span><span class="rl-progress__value">2,840 / 8,000</span></span></div></div></div>
```
