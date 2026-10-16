# ActionBar

The sticky bar at the bottom of a task screen: an optional total and the one button that moves the task on.

It replaces the bottom navigation on task screens and respects the bottom safe area. You provide the button label and, when money is involved, the total.

- One button. Its label is the action: "Continue", "Add Member", "Collect ₹1,500".
- The total sits to the left of the button in `rl-actionbar__sum`; hide it on steps where there is nothing to add up.
- Give the screen `rl-app--task` so its content clears the bar.

## Markup (from the design system preview)

```html
<div class="rl-root"><div class="rl-actionbar"><div class="rl-actionbar__in"><div class="rl-actionbar__sum"><span>Total</span><strong>₹4,500</strong></div><button class="rl-button" type="button">Continue</button></div></div></div>
```
