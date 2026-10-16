# Sheet

A bottom sheet: a panel that slides up over a `scrim` for a short list of choices.

You provide the title and the rows. Open it by adding `is-open` to the `rl-sheet` and the `rl-scrim`; the script in the Admin Home preview shows the full behaviour (one sheet at a time, focus moves in, focus returns to the opener on close).

- Rows are `rl-sheet__item`, 60px tall: an icon chip, a label, and either a chevron (an action) or the `volt` check (the current choice in a radio list).
- It closes on the scrim, the close button, choosing a row, or Escape.
- Use for the create actions, the branch switcher, the result of a check-in (see CheckInSheet) and quick logging on Member Home (see MemberWaterSheet). Anything with a form gets its own screen. Past about seven rows, split the list into groups with a `rl-sheet__label` above each, as the Admin's create sheet does; past about ten, use a screen.
- A destructive row (`rl-sheet__item--danger`) is `danger` text with a `danger-soft` chip, last in its list, with no chevron.
- On wide screens it stays bottom-anchored, 560px wide at most.

## Markup (from the design system preview)

```html
<div class="rl-root"><div class="rl-scrim is-open" data-close></div>
<div class="rl-sheet is-open" id="rl-sheet-create" role="dialog" aria-modal="true" aria-labelledby="rl-sheet-create-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="rl-sheet-create-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <p class="rl-sheet__label" id="rl-sheet-create-g1" style="margin-top:var(--space-1)">Members</p>
  <ul class="rl-sheet__list" aria-labelledby="rl-sheet-create-g1"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Member</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">New Subscription</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Collect Payment</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Mark Attendance</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Follow-up</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Book Session</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
  <p class="rl-sheet__label" id="rl-sheet-create-g2">Staff and expenses</p>
  <ul class="rl-sheet__list" aria-labelledby="rl-sheet-create-g2"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Trainer</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Receptionist</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Assign Task</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Expense</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<div class="rl-sheet" id="rl-sheet-branch" role="dialog" aria-modal="true" aria-labelledby="rl-sheet-branch-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="rl-sheet-branch-title">Switch branch</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list" role="radiogroup" aria-label="Branch"><li><button class="rl-sheet__item" type="button" role="radio" aria-checked="true"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Indiranagar<span class="rl-row__meta">612 active members</span></span><span class="rl-sheet__check"><Icon class="rl-icon rl-icon--sm"/></span></button></li><li><button class="rl-sheet__item" type="button" role="radio" aria-checked="false"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Koramangala<span class="rl-row__meta">548 active members</span></span></button></li><li><button class="rl-sheet__item" type="button" role="radio" aria-checked="false"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">HSR Layout<span class="rl-row__meta">431 active members</span></span></button></li><li><button class="rl-sheet__item" type="button" role="radio" aria-checked="false"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Whitefield<span class="rl-row__meta">386 active members</span></span></button></li></ul>
</div></div>
```
