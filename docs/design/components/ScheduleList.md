# ScheduleList

The next sessions today: time, a type tag, a title, and who is involved.

Use in a `rl-card` on Admin Home with a "View all" link in the section head. Show the next three or four items. You provide the time, the type (PT, Class or Appointment), the title, and one line naming the trainer and either the member ("Kavya Shetty with Rohan Mehta") or the headcount ("Arjun Rao, 16/20 booked").

- Mark the session in progress with `is-now` on the row and a `rl-tag--now` tag under the time. If nothing is in progress, mark the next one and label it "Next".
- The type is a word in a tag, never a colour code.
- On Trainer Home the list is the trainer's own day: put an `rl-agenda__summary` above the rows ("2 of 6 sessions done" with a bar), lead each PT row with the member's name, and mark the next session with `rl-tag--next`.

```html
<ul class="rl-card rl-agenda">
  <li><a class="rl-agenda__row is-now" href="…">
    <span class="rl-agenda__time">6:00 PM<br><span class="rl-tag rl-tag--now">Now</span></span>
    <span><span class="rl-agenda__top"><span class="rl-tag">Class</span><span class="rl-row__title">HIIT Burn</span></span>
      <span class="rl-row__meta">Arjun Rao, 16/20 booked</span></span>
  </a></li>
</ul>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><ul class="rl-card rl-agenda"><li><a class="rl-agenda__row is-now" href="#"><span class="rl-agenda__time">6:00 PM<br><span class="rl-tag rl-tag--now">Now</span></span><span><span class="rl-agenda__top"><span class="rl-tag">Class</span><span class="rl-row__title">HIIT Burn</span></span><span class="rl-row__meta">Arjun Rao, 16/20 booked</span></span></a></li><li><a class="rl-agenda__row" href="#"><span class="rl-agenda__time">6:30 PM</span><span><span class="rl-agenda__top"><span class="rl-tag">PT</span><span class="rl-row__title">Strength session</span></span><span class="rl-row__meta">Kavya Shetty with Rohan Mehta</span></span></a></li><li><a class="rl-agenda__row" href="#"><span class="rl-agenda__time">7:00 PM</span><span><span class="rl-agenda__top"><span class="rl-tag">Class</span><span class="rl-row__title">Power Yoga</span></span><span class="rl-row__meta">Neha Iyer, 12/20 booked</span></span></a></li><li><a class="rl-agenda__row" href="#"><span class="rl-agenda__time">7:30 PM</span><span><span class="rl-agenda__top"><span class="rl-tag">Appointment</span><span class="rl-row__title">Membership tour</span></span><span class="rl-row__meta">Imran Khan with Sneha Kulkarni</span></span></a></li></ul></div>
```
