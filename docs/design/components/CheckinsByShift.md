# CheckinsByShift

Who checked in today, split by shift: one row each for members, trainers and receptionists, and one column each for morning, afternoon and evening.

Use once on Admin Home, under Needs attention. You provide the three counts for each row, a short note for each row and where each row leads. The columns are the branch's own sessions from its opening hours (Indiranagar: Morning 5 to 10 AM, Afternoon 12 to 4 PM, Evening 5 PM to now), one column per session; a check-in during a break counts in the next session. The shift that is happening now ends in "now", and its count is the total so far.

- Each row is one link, 64px tall. Members opens Attendance; Trainers and Receptionists open the Staff side of Attendance, filtered to that role.
- The note is a few words: the total so far for members, and how many of the people working today have checked in for staff ("3 of 4 in").
- A zero is shown as 0 in `ink-muted`, never left blank.
- Counts are `metric`-weight numbers, centred under the shift name. Do not colour them; this card reports, it does not warn.
- The column headings are hidden from screen readers; each row has an `aria-label` that reads its counts with the shift names.

```html
<div class="rl-card rl-shifts">
  <div class="rl-shifts__head" aria-hidden="true"><span></span>
    <span class="rl-shifts__h">Morning<small>6 AM–12</small></span>
    <span class="rl-shifts__h">Afternoon<small>12–5 PM</small></span>
    <span class="rl-shifts__h">Evening<small>5 PM–now</small></span>
  </div>
  <ul class="rl-shifts__list">
    <li><a class="rl-shifts__row" href="…" aria-label="Members: morning 98, afternoon 29, evening 21. 148 so far">
      <span class="rl-shifts__who"><span class="rl-row__title">Members</span><span class="rl-row__meta">148 so far</span></span>
      <span class="rl-shifts__n">98</span><span class="rl-shifts__n">29</span><span class="rl-shifts__n">21</span>
    </a></li>
  </ul>
</div>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-card rl-shifts"><div class="rl-shifts__head" aria-hidden="true"><span></span><span class="rl-shifts__h">Morning<small>5–10 AM</small></span><span class="rl-shifts__h">Afternoon<small>12–4 PM</small></span><span class="rl-shifts__h is-now">Evening<small>5 PM–now</small></span></div><ul class="rl-shifts__list"><li><a class="rl-shifts__row" href="#" data-shift-go="members" aria-label="Members: morning 106, afternoon 17, evening 22. 145 so far"><span class="rl-shifts__who"><span class="rl-row__title">Members</span><span class="rl-row__meta">145 so far</span></span><span class="rl-shifts__n">106</span><span class="rl-shifts__n">17</span><span class="rl-shifts__n">22</span></a></li><li><a class="rl-shifts__row" href="#" data-shift-go="trainers" aria-label="Trainers: morning 2, afternoon 0, evening 1. 3 of 4 checked in"><span class="rl-shifts__who"><span class="rl-row__title">Trainers</span><span class="rl-row__meta">3 of 4 checked in</span></span><span class="rl-shifts__n">2</span><span class="rl-shifts__n is-zero">0</span><span class="rl-shifts__n">1</span></a></li><li><a class="rl-shifts__row" href="#" data-shift-go="desk" aria-label="Receptionists: morning 0, afternoon 1, evening 0. 1 of 2 checked in"><span class="rl-shifts__who"><span class="rl-row__title">Receptionists</span><span class="rl-row__meta">1 of 2 checked in</span></span><span class="rl-shifts__n is-zero">0</span><span class="rl-shifts__n">1</span><span class="rl-shifts__n is-zero">0</span></a></li></ul></div></div>
```
