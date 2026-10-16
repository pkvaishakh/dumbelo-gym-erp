# GoalCard

The member's goal and how far along it they are.

Use at the top of the Progress tab. You provide the goal, the starting value, the current value and the target. It is the membership card's layout with other content: a pill and the goal's name on top with the target on the right, the change so far as a `figure`, a bar from start to target, and the start and what is left under the bar.

- The pill says where they stand in words ("On track") with an arrow. It is never colour alone.
- Write the change with a real minus sign: "−4.8 kg".

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-pass">
  <div class="rl-pass__top"><span class="rl-pill rl-pill--soft"><Icon class="rl-icon rl-icon--xs"/>On track</span><span class="rl-pass__plan">Fat Loss</span><span class="rl-pass__link" style="font-weight:400;color:var(--ink-muted)">Goal 68.0 kg</span></div>
  <p class="rl-figure"><span data-w-lost>−4.8</span> <small>kg since 29 Jul</small></p>
  <span class="rl-bar" role="img" aria-label="4.8 of 8.0 kg lost"><span class="rl-bar__fill" data-w-bar style="--v:0.600"></span></span>
  <div class="rl-pass__dates"><span>Started at 76.0 kg</span><span data-w-left>3.2 kg to go</span></div>
</div></div>
```
