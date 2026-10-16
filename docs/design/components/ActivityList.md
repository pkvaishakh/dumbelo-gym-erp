# ActivityList

The latest things that happened in the gym: an avatar or icon, one line, and a relative time.

Use in a `rl-card` on Admin Home with a "View all" link. Show five items. You provide who, what and when. Lead with the person's name in bold, then a plain verb: "Rohan Mehta paid ₹4,500".

- Use an initials avatar (`rl-avatar rl-avatar--sm`) when the item is about a member doing something themselves; use an icon chip (`rl-chipicon`) for payments, renewals and staff actions.
- One line only; it truncates. Keep the amount or plan name inside the first 28 characters.

```html
<ul class="rl-card rl-activity">
  <li><div class="rl-activity__row">
    <span class="rl-chipicon" aria-hidden="true"><!-- 20px icon --></span>
    <div class="rl-activity__text"><p class="rl-row__body"><strong>Rohan Mehta</strong> paid ₹4,500</p><p class="rl-row__meta">4 min ago</p></div>
  </div></li>
</ul>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><ul class="rl-card rl-activity"><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__body"><strong>Rohan Mehta</strong> paid ₹4,500</p><p class="rl-row__meta">4 min ago</p></div></div></li><li><div class="rl-activity__row"><span class="rl-avatar rl-avatar--sm" aria-hidden="true">DJ</span><div class="rl-activity__text"><p class="rl-row__body"><strong>Divya Joshi</strong> checked in</p><p class="rl-row__meta">9 min ago</p></div></div></li><li><div class="rl-activity__row"><span class="rl-avatar rl-avatar--sm" aria-hidden="true">AV</span><div class="rl-activity__text"><p class="rl-row__body"><strong>Aditya Verma</strong> joined on Monthly</p><p class="rl-row__meta">12 min ago</p></div></div></li><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__body"><strong>Priya Nair</strong> renewed Annual</p><p class="rl-row__meta">38 min ago</p></div></div></li><li><div class="rl-activity__row"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div class="rl-activity__text"><p class="rl-row__body"><strong>Imran Khan</strong> marked attendance</p><p class="rl-row__meta">52 min ago</p></div></div></li></ul></div>
```
