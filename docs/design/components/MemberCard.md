# MemberCard

A compact card for one member: photo, name, status badge and their last check-in time.

Use in Recent members on Receptionist Home, six cards in an `rl-scroller rl-scroller--row` that scrolls sideways at every width. You provide the photo or initials, the name, the status and the time. The whole card is a link to the member's profile.

- Newest check-in first. The first cards are the same people, at the same times, as the check-ins in Today's activity.
- One line for the name; it truncates.

```html
<a class="rl-member rl-pressable" href="…">
  <span class="rl-photo" aria-hidden="true">SK</span>
  <span class="rl-member__name">Sana Kapoor</span>
  <span class="rl-status rl-status--active">Active</span>
  <span class="rl-member__time">8:38 AM</span>
</a>
```

## Markup (from the design system preview)

```html
<div class="rl-root"><div class="rl-scroller rl-scroller--row" style="margin:0;padding:4px 0 16px"><a class="rl-member rl-pressable" href="#" aria-label="Sana Kapoor, Active, checked in at 8:38 AM"><span class="rl-photo" aria-hidden="true">SK</span><span class="rl-member__name">Sana Kapoor</span><span class="rl-status rl-status--active">Active</span><span class="rl-member__time">8:38 AM</span></a><a class="rl-member rl-pressable" href="#" aria-label="Vikram Shetty, Expiring, checked in at 8:34 AM"><span class="rl-photo" aria-hidden="true">VS</span><span class="rl-member__name">Vikram Shetty</span><span class="rl-status rl-status--expiring">Expiring</span><span class="rl-member__time">8:34 AM</span></a><a class="rl-member rl-pressable" href="#" aria-label="Meenal Shah, Active, checked in at 8:27 AM"><span class="rl-photo" aria-hidden="true">MS</span><span class="rl-member__name">Meenal Shah</span><span class="rl-status rl-status--active">Active</span><span class="rl-member__time">8:27 AM</span></a><a class="rl-member rl-pressable" href="#" aria-label="Farhan Ali, Payment due, checked in at 8:21 AM"><span class="rl-photo" aria-hidden="true">FA</span><span class="rl-member__name">Farhan Ali</span><span class="rl-status rl-status--due">Payment due</span><span class="rl-member__time">8:21 AM</span></a></div></div>
```
