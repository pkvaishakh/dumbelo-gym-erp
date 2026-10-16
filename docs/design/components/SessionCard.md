# SessionCard

The member's next booked session: time, type and length, a countdown, the trainer and the focus.

Use once on Member Home under a section head that carries a "Book Session" link. You provide the time, the session type and length, the countdown text, the trainer's photo or initials and name, and the focus. "View Session" is a small secondary button.

- The countdown is a `volt-soft` pill with a clock icon, in hours and minutes: "In 1 h 45 min". Under an hour, minutes only.
- Empty state, when nothing is booked: `rl-session--empty` with an icon, "No session booked", one line of encouragement and a "Book Session" button.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-card rl-session">
  <div class="rl-session__when"><div><p class="rl-session__time">11:00 AM</p><p class="rl-row__meta">Personal Training, 45 minutes</p></div><span class="rl-pill rl-pill--soft"><Icon class="rl-icon rl-icon--xs"/>In 1 h 45 min</span></div>
  <div class="rl-session__who"><span class="rl-photo" aria-hidden="true">AR</span><span><span class="rl-row__title">Trainer: Arjun</span><span class="rl-row__meta">Focus: Chest &amp; Triceps</span></span><a class="rl-button rl-button--secondary rl-button--sm" href="#">View Session</a></div>
</div><div class="rl-card rl-session rl-session--empty"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><div><p class="rl-row__title">No session booked</p><p class="rl-row__meta">Book time with Arjun to keep your plan moving.</p></div><a class="rl-button rl-button--secondary rl-button--sm" href="#">Book Session</a></div></div>
```
