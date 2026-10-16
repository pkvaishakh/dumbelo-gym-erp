# ProfileHeader

The top of a profile: a large photo, the name, the member ID with a status badge, and the actions for this member.

You provide the photo or initials, the name, the ID, the status, and up to two main actions. Lay the actions out in `rl-actions`: the primary action first (`rl-button`), one secondary beside it, and a contact row of two small secondary buttons (Call, Message) under them.

- One primary action only, chosen by role and state: Check In, Renew, or Log Workout.
- When the primary action is done, replace the button with an `rl-statusline` that says so ("Checked in at 8:41 AM").
- A blocking condition goes above the buttons as an `rl-statusline` in `danger` with an icon, in words.
- Anything less frequent belongs in the more-actions sheet, not here.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-identity"><span class="rl-photo rl-photo--xl" aria-hidden="true">RK</span><div class="rl-identity__text"><h2 class="rl-identity__name">Rahul Kumar</h2><p class="rl-identity__meta" style="margin:0"><span>RL-2041</span><span class="rl-status rl-status--active">Active</span></p></div></div><div class="rl-actions"><button class="rl-button" type="button">Check In</button><a class="rl-button rl-button--secondary" href="#">Collect Payment</a><div class="rl-actions__contact"><a class="rl-button rl-button--secondary rl-button--sm" href="#"><Icon class="rl-icon rl-icon--sm"/>Call</a><a class="rl-button rl-button--secondary rl-button--sm" href="#"><Icon class="rl-icon rl-icon--sm"/>Message</a></div></div></div>
```
