# MemberRow

One member in a list: photo, name, member ID and plan, status badge, and the date that matters.

Use in a `rl-card rl-mlist` list. You provide the member and the link target. The whole row is the link, at least 68px tall. On a phone it is two lines: name and StatusBadge on the first, "RL-2041 • Premium + PT" and the note on the second. From 768px it spreads into columns (see MembersListWide).

- The note is one short phrase chosen by state: "Ends 28 Oct", "Ends in 4 days", "Ends today", "Ended 28 Sep", "₹1,500 due", "Until 20 Oct". Add the year only when it is not this year. Add `rl-mrow__note--warn` or `rl-mrow__note--alert` when it needs attention.
- Long names end in an ellipsis; the badge and the note never wrap or shrink.
- Every row opens that member's profile, filled from their record (see MemberProfileExpiring).
- No buttons in the row. Use SearchResult when the row needs an inline Check In.
- For a day's attendance use VisitRow: the same layout with the check-in time in place of the badge.
- The same row lists staff on StaffList: role and members or shift on the second line, today's note on the right. There it is a `button`, because it opens a sheet.

```html
<ul class="rl-card rl-mlist">
  <li><a class="rl-mrow" href="/members/RL-2041">
    <span class="rl-photo" aria-hidden="true">RK</span>
    <span class="rl-row__title rl-mrow__name">Rahul Kumar</span>
    <span class="rl-row__meta rl-mrow__meta">RL-2041<span class="rl-mrow__inline"> • Premium + PT</span></span>
    <span class="rl-mrow__cell rl-mrow__cell--plan">Premium + PT</span>
    <span class="rl-mrow__cell rl-mrow__cell--visit">Yesterday</span>
    <span class="rl-status rl-status--active">Active</span>
    <span class="rl-mrow__note">Ends 28 Oct</span>
  </a></li>
</ul>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><ul class="rl-card rl-mlist"><li><a class="rl-mrow" href="#" data-member="RL-2041"><span class="rl-photo" aria-hidden="true">RK</span><span class="rl-row__title rl-mrow__name">Rahul Kumar</span><span class="rl-row__meta rl-mrow__meta">RL-2041<span class="rl-mrow__inline"> • Premium + PT</span></span><span class="rl-mrow__cell rl-mrow__cell--plan">Premium + PT</span><span class="rl-mrow__cell rl-mrow__cell--visit">Yesterday</span><span class="rl-status rl-status--active">Active</span><span class="rl-mrow__note">Ends 28 Oct</span></a></li><li><a class="rl-mrow" href="#" data-member="RL-1688"><span class="rl-photo" aria-hidden="true">KI</span><span class="rl-row__title rl-mrow__name">Karthik Iyer</span><span class="rl-row__meta rl-mrow__meta">RL-1688<span class="rl-mrow__inline"> • Monthly + PT</span></span><span class="rl-mrow__cell rl-mrow__cell--plan">Monthly + PT</span><span class="rl-mrow__cell rl-mrow__cell--visit">Today, 8:09 AM</span><span class="rl-status rl-status--expiring">Expiring</span><span class="rl-mrow__note rl-mrow__note--warn">Ends today</span></a></li><li><a class="rl-mrow" href="#" data-member="RL-1723"><span class="rl-photo" aria-hidden="true">FA</span><span class="rl-row__title rl-mrow__name">Farhan Ali</span><span class="rl-row__meta rl-mrow__meta">RL-1723<span class="rl-mrow__inline"> • Monthly + PT</span></span><span class="rl-mrow__cell rl-mrow__cell--plan">Monthly + PT</span><span class="rl-mrow__cell rl-mrow__cell--visit">Today, 8:21 AM</span><span class="rl-status rl-status--due">Payment due</span><span class="rl-mrow__note rl-mrow__note--warn">₹1,500 due</span></a></li><li><a class="rl-mrow" href="#" data-member="RL-1532"><span class="rl-photo" aria-hidden="true">RM</span><span class="rl-row__title rl-mrow__name">Raghav Menon</span><span class="rl-row__meta rl-mrow__meta">RL-1532<span class="rl-mrow__inline"> • Monthly</span></span><span class="rl-mrow__cell rl-mrow__cell--plan">Monthly</span><span class="rl-mrow__cell rl-mrow__cell--visit">27 Sep</span><span class="rl-status rl-status--expired">Expired</span><span class="rl-mrow__note rl-mrow__note--alert">Ended 28 Sep</span></a></li></ul></div>
```
