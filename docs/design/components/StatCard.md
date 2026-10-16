# StatCard

One figure for today: an icon, a large number, a short label and a trend.

Use in the overview row at the top of Admin Home, inside `rl-scroller`, which scrolls sideways on a phone with the next card peeking and becomes four across from 768px (five with `rl-scroller--five`). You provide the icon, the value, the label and the trend text. The whole card is a link to that figure's detail.

- The value is `metric`; the label is one short phrase; the trend is an arrow icon plus signed text that names its comparison ("+12% vs yesterday").
- Instead of a trend, a card may carry a status line (`rl-stat__note`): a short fact ("12 since 8 AM") or a StatusBadge. The status line is optional.
- While loading, show a skeleton card of the same size built from `rl-skel` blocks.
- Do not colour the value or the trend, and do not put more than five cards in the row. Five only on Admin Home, with `rl-scroller--five`.

```html
<a class="rl-stat rl-pressable" href="…">
  <span class="rl-stat__icon"><!-- 20px icon --></span>
  <p class="rl-stat__value">₹48,650</p>
  <p class="rl-stat__label">Today's revenue</p>
  <p class="rl-trend"><!-- 16px arrow --><span>+12% vs yesterday</span></p>
</a>
```

## Markup (from the design system preview)

```html
<div class="rl-root"><div class="rl-scroller" style="margin:0;padding:4px 0 16px"><a class="rl-stat rl-pressable" href="#"><span class="rl-stat__icon"><Icon class="rl-icon rl-icon--sm"/></span><p class="rl-stat__value">₹48,650</p><p class="rl-stat__label">Today’s revenue</p><p class="rl-trend"><Icon class="rl-icon rl-icon--xs"/><span>+12% vs yesterday</span></p></a><a class="rl-stat rl-pressable" href="#"><span class="rl-stat__icon"><Icon class="rl-icon rl-icon--sm"/></span><p class="rl-stat__value">35</p><p class="rl-stat__label">Expired</p><p class="rl-stat__note">Not renewed yet</p></a><div class="rl-stat" aria-hidden="true"><span class="rl-skel" style="width:36px;height:36px;border-radius:var(--radius-sm)"></span><span class="rl-skel" style="width:72%;height:24px;margin-top:16px"></span><span class="rl-skel" style="width:56%;height:12px;margin-top:12px"></span><span class="rl-skel" style="width:88%;height:12px;margin-top:16px"></span></div></div></div>
```
