# ActionTile

A quick-action tile: an icon and a title-case label, at least 64px tall.

Use four in a 2×2 `rl-tiles` grid. You provide the icon and the label. The two actions done most often are `rl-tile--primary` (`ink` fill, `on-ink` label, `volt` icon); the others are the default (`ground` fill, 1px `field-line` edge).

- Two primary tiles at most. Labels are two words; they may wrap to two lines on a phone.
- `rl-tile--accent` is the one `volt` tile, 72px tall, with a hint line under its label and a chevron: Check In Member on Receptionist Home. Put it full width at the top of an `rl-quick` grid.
- `rl-tile--stack` puts the icon above the label for three tiles in one row under the accent tile.
- A tile starts a task. Navigation belongs in the bottom navigation.

```html
<div class="rl-tiles">
  <button class="rl-tile rl-tile--primary rl-pressable" type="button"><!-- 24px icon --><span>Add Member</span></button>
  <button class="rl-tile rl-pressable" type="button"><!-- 24px icon --><span>New Subscription</span></button>
</div>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo" style="display:grid;gap:var(--space-6)"><div class="rl-tiles"><button class="rl-tile rl-tile--primary rl-pressable" type="button"><Icon class="rl-icon"/><span>Add Member</span></button><button class="rl-tile rl-tile--primary rl-pressable" type="button"><Icon class="rl-icon"/><span>Collect Payment</span></button><button class="rl-tile rl-pressable" type="button"><Icon class="rl-icon"/><span>New Subscription</span></button><button class="rl-tile rl-pressable" type="button"><Icon class="rl-icon"/><span>Mark Attendance</span></button></div><div class="rl-quick">
  <button class="rl-tile rl-tile--accent rl-pressable" type="button" data-search-open><Icon class="rl-icon"/><span class="rl-tile__text">Check In Member<span class="rl-tile__hint">Search or scan, then one tap</span></span><Icon class="rl-icon rl-icon--sm"/></button>
  <button class="rl-tile rl-tile--stack rl-pressable" type="button"><Icon class="rl-icon"/><span>Add Member</span></button><button class="rl-tile rl-tile--stack rl-pressable" type="button"><Icon class="rl-icon"/><span>Collect Payment</span></button><button class="rl-tile rl-tile--stack rl-pressable" type="button"><Icon class="rl-icon"/><span>New Subscription</span></button>
</div></div>
```
