# WeightCard

Recent progress: current weight as the large figure, the change since the start, and a small line chart of the last eight weeks.

Use once on Member Home under a section head with a "View Progress" link. You provide the current weight and when it was updated, the starting weight, the change, and the weekly points.

- Show the change as a `volt-soft` pill with a trend icon and words that say whether it suits the goal: "−4.8 kg, on track" for a fat-loss goal. Do not rely on the minus sign or the colour.
- The chart is a 2px `ink` line with a `volt` end point on a trimmed axis (here 70 to 76 kg) and no area fill. Each point shows its value on tap, hover or focus.
- The figure in the card equals the last point on the chart.

## Markup (from the design system preview)

```html
<div class="rl-root demo rl-app" style="min-height:0;padding-bottom:0;background:none"><div class="rl-card rl-weight">
  <div class="rl-weight__top">
    <div><p class="rl-figure">71.2 <small>kg</small></p><p class="rl-row__meta">Updated today</p></div>
    <div class="rl-weight__side"><span class="rl-pill rl-pill--soft"><Icon class="rl-icon rl-icon--xs"/>−4.8 kg, on track</span><span class="rl-row__meta">Started at 76.0 kg</span></div>
  </div>
  <div class="rl-chart rl-chart--sm" role="group" aria-label="Weight in kilograms, last 8 weeks">
    <div class="rl-chart__y" aria-hidden="true"><span style="--p:0">70</span><span style="--p:0.5">73</span><span style="--p:1">76</span></div>
    <div class="rl-chart__plot"><div class="rl-chart__grid" aria-hidden="true"><span style="--p:0"></span><span style="--p:0.5"></span><span style="--p:1"></span></div><Icon class="rl-chart__line"/><span class="rl-chart__dot" style="--x:0.9375;--v:0.2000"></span><span class="rl-chart__marker"></span><div class="rl-chart__cols"><button class="rl-chart__col" type="button" style="--v:0.6833;--x:0.0625" data-label="Sun 16 Aug" data-value="74.1 kg" aria-label="Sun 16 Aug: 74.1 kg"></button><button class="rl-chart__col" type="button" style="--v:0.6333;--x:0.1875" data-label="Sun 23 Aug" data-value="73.8 kg" aria-label="Sun 23 Aug: 73.8 kg"></button><button class="rl-chart__col" type="button" style="--v:0.5333;--x:0.3125" data-label="Sun 30 Aug" data-value="73.2 kg" aria-label="Sun 30 Aug: 73.2 kg"></button><button class="rl-chart__col" type="button" style="--v:0.5000;--x:0.4375" data-label="Sun 6 Sep" data-value="73.0 kg" aria-label="Sun 6 Sep: 73.0 kg"></button><button class="rl-chart__col" type="button" style="--v:0.4000;--x:0.5625" data-label="Sun 13 Sep" data-value="72.4 kg" aria-label="Sun 13 Sep: 72.4 kg"></button><button class="rl-chart__col" type="button" style="--v:0.3500;--x:0.6875" data-label="Sun 20 Sep" data-value="72.1 kg" aria-label="Sun 20 Sep: 72.1 kg"></button><button class="rl-chart__col" type="button" style="--v:0.2667;--x:0.8125" data-label="Sun 27 Sep" data-value="71.6 kg" aria-label="Sun 27 Sep: 71.6 kg"></button><button class="rl-chart__col" type="button" style="--v:0.2000;--x:0.9375" data-label="Sun 4 Oct" data-value="71.2 kg" aria-label="Sun 4 Oct: 71.2 kg"></button></div><div class="rl-chart__tip" role="status"></div></div>
    <div class="rl-chart__x rl-chart__x--free"><span style="--x:0.0625">16 Aug</span><span style="--x:0.4375">6 Sep</span><span style="--x:0.9375">4 Oct</span></div>
  </div>
</div></div>
```
