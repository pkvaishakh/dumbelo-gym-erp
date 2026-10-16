# DayStrip

Seven days in a row, one selected. It chooses the day a screen is showing.

Use at the top of a screen that shows one day at a time, pinned under the title. You provide the days and the input `name`. Each day is a radio button drawn as a 56px tile: the weekday above, the date below. The last tile is today and says "Today" in place of the weekday. The selected day is filled with `ink`.

- Seven days, oldest on the left, today on the right. No scrolling and no future days.
- It changes everything below it at once. Do not pair it with a second date control.
- Give each input an `aria-label` with the full date and that day's total, such as "Sunday 4 October, 206 check-ins".
- From 768px it stops at `column-max`.

```html
<div class="rl-daystrip" role="radiogroup" aria-label="Day">
  <label class="rl-day"><input type="radio" name="day" value="2026-10-04" aria-label="Sunday 4 October, 206 check-ins"><span><small>Sun</small><b>4</b></span></label>
  <label class="rl-day"><input type="radio" name="day" value="2026-10-05" checked aria-label="Today, Monday 5 October, 64 check-ins"><span><small>Today</small><b>5</b></span></label>
</div>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-daystrip" role="radiogroup" aria-label="Day"><label class="rl-day"><input type="radio" name="ds-day" value="2026-09-29" aria-label="Tuesday 29 September, 301 check-ins"><span><small>Tue</small><b>29</b></span></label><label class="rl-day"><input type="radio" name="ds-day" value="2026-09-30" aria-label="Wednesday 30 September, 296 check-ins"><span><small>Wed</small><b>30</b></span></label><label class="rl-day"><input type="radio" name="ds-day" value="2026-10-01" aria-label="Thursday 1 October, 312 check-ins"><span><small>Thu</small><b>1</b></span></label><label class="rl-day"><input type="radio" name="ds-day" value="2026-10-02" aria-label="Friday 2 October, 287 check-ins"><span><small>Fri</small><b>2</b></span></label><label class="rl-day"><input type="radio" name="ds-day" value="2026-10-03" aria-label="Saturday 3 October, 264 check-ins"><span><small>Sat</small><b>3</b></span></label><label class="rl-day"><input type="radio" name="ds-day" value="2026-10-04" aria-label="Sunday 4 October, 206 check-ins"><span><small>Sun</small><b>4</b></span></label><label class="rl-day"><input type="radio" name="ds-day" value="2026-10-05" checked aria-label="Today, Monday 5 October, 64 check-ins"><span><small>Today</small><b>5</b></span></label></div></div>
```
