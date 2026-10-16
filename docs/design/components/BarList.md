# BarList

A short ranked comparison: one bar per row, with the name on the left and the value in words on the right.

Use to compare parts of a total or a handful of people: revenue by plan, expenses by category, sessions by trainer, check-ins by hour. You provide the rows. Each bar is `ink`, 8px tall, and its length is the row's share of the largest value in the list, so the longest bar is always full.

- Always print the value. The bar is for comparing at a glance, never the only way to read the number.
- One colour for every bar. Do not use `volt`, and do not colour rows differently.
- Keep to about seven rows. Fold the rest into "Other", last.
- Use it in place of a pie or donut.

```html
<ul class="rl-barlist">
  <li>
    <div class="rl-barlist__top"><span>Premium</span><span>₹72,000</span></div>
    <span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:1"></span></span>
  </li>
</ul>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-card rl-card--pad"><ul class="rl-barlist"><li><div class="rl-barlist__top"><span>Monthly</span><span>₹61,500</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.854"></span></span></li><li><div class="rl-barlist__top"><span>Quarterly</span><span>₹67,500</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.938"></span></span></li><li><div class="rl-barlist__top"><span>Premium</span><span>₹72,000</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:1.000"></span></span></li><li><div class="rl-barlist__top"><span>Annual</span><span>₹45,000</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.625"></span></span></li><li><div class="rl-barlist__top"><span>Personal training</span><span>₹54,000</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.750"></span></span></li><li><div class="rl-barlist__top"><span>Other</span><span>₹5,340</span></div><span class="rl-bar" aria-hidden="true"><span class="rl-bar__fill" style="--v:0.074"></span></span></li></ul></div></div>
```
