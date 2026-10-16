# MeasurementList

Body measurements as a list: the part, the latest value and the change since the start.

Use on the Progress tab. You provide the rows and the two dates in the footer. The change is an arrow and a signed number, in `ink`. The footer says what the change is measured from, when the values were last recorded and when the next ones are due.

- No colour on the changes. Whether a change is good depends on the goal, and the trainer says that, not the list.
- Recording opens from the "Record" link in the section head.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-card"><ul class="rl-measures"><li class="rl-measure"><span>Chest</span><span class="rl-measure__value">98 cm</span><span class="rl-measure__change"><Icon class="rl-icon rl-icon--xs"/>−3 cm</span></li><li class="rl-measure"><span>Waist</span><span class="rl-measure__value">86 cm</span><span class="rl-measure__change"><Icon class="rl-icon rl-icon--xs"/>−6 cm</span></li><li class="rl-measure"><span>Hips</span><span class="rl-measure__value">97 cm</span><span class="rl-measure__change"><Icon class="rl-icon rl-icon--xs"/>−3 cm</span></li><li class="rl-measure"><span>Arms</span><span class="rl-measure__value">34 cm</span><span class="rl-measure__change"><Icon class="rl-icon rl-icon--xs"/>+1 cm</span></li><li class="rl-measure"><span>Thighs</span><span class="rl-measure__value">56 cm</span><span class="rl-measure__change"><Icon class="rl-icon rl-icon--xs"/>−2 cm</span></li></ul><p class="rl-cardfoot">Changes since 29 Jul. Last recorded Sun 27 Sep; this week’s are due today.</p></div></div>
```
