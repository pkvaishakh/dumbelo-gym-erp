# StreakCard

The attendance streak: a headline, one warm sentence, and the week from Monday to Sunday.

Use once on Member Home. You provide the streak length and which days of this week were attended. Checked-in days are `volt` dots with a check; today, if not yet checked in, is an outlined dot labelled "Today"; days not attended are outlined without emphasis.

- The headline is "🔥 8 Day Streak". The flame is one of the only two emoji in the app.
- The sentence says what happened and what today adds: "You've checked in 8 days in a row. Check in today to make it 9."
- Hide the card when the streak is under two days; never show a broken-streak message here.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><section class="rl-streak" aria-label="Attendance streak">
  <h2 class="rl-streak__title">🔥 8 Day Streak</h2>
  <p class="rl-streak__text">You’ve checked in 8 days in a row. Check in today to make it 9.</p>
  <ol class="rl-week" aria-label="This week"><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Mon</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Tue</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Wed</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Thu</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Fri</li><li><span class="rl-week__dot" aria-label="Checked in"><Icon class="rl-icon rl-icon--xs"/></span>Sat</li><li class="is-today"><span class="rl-week__dot" aria-label="Not checked in yet"></span>Today</li></ol>
</section></div>
```
