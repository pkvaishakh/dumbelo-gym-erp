# VisitRow

One check-in in the day's attendance: who, and when they checked in.

Use in a `rl-card rl-mlist rl-mlist--compact` list. It is the MemberRow layout with the right-hand side changed: the check-in time on the first line in place of the StatusBadge, and nothing on the second. The gym records only who checked in and when, so a row never says whether the member is still inside. The row is a `button`, at least 68px tall, and opens the VisitSheet.

- Sort by check-in time, newest first.
- No live dot, no "In the gym", no "Left": there is no check-out to show.
- `rl-mlist--compact` keeps the two-line layout at every width. Use it whenever a row list sits in one column of a two-column screen.
- The membership status is not shown in the row. It is on the VisitSheet.

```html
<ul class="rl-card rl-mlist rl-mlist--compact">
  <li><button class="rl-mrow" type="button" aria-haspopup="dialog">
    <span class="rl-photo" aria-hidden="true">SK</span>
    <span class="rl-row__title rl-mrow__name">Sana Kapoor</span>
    <span class="rl-row__meta rl-mrow__meta">RL-2210 • Annual</span>
    <span class="rl-mrow__time">8:38 AM</span>
  </button></li>
</ul>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><ul class="rl-card rl-mlist rl-mlist--compact"><li><button class="rl-mrow" type="button" data-visit="t1" aria-haspopup="dialog"><span class="rl-photo" aria-hidden="true">SK</span><span class="rl-row__title rl-mrow__name">Sana Kapoor</span><span class="rl-row__meta rl-mrow__meta">RL-2210 • Annual</span><span class="rl-mrow__time">8:38 AM</span></button></li><li><button class="rl-mrow" type="button" data-visit="t4" aria-haspopup="dialog"><span class="rl-photo" aria-hidden="true">FA</span><span class="rl-row__title rl-mrow__name">Farhan Ali</span><span class="rl-row__meta rl-mrow__meta">RL-1723 • Monthly + PT</span><span class="rl-mrow__time">8:21 AM</span></button></li><li><button class="rl-mrow" type="button" data-visit="t9" aria-haspopup="dialog"><span class="rl-photo" aria-hidden="true">RM</span><span class="rl-row__title rl-mrow__name">Rohan Mehta</span><span class="rl-row__meta rl-mrow__meta">RL-2144 • Quarterly + PT</span><span class="rl-mrow__time">7:31 AM</span></button></li></ul></div>
```
