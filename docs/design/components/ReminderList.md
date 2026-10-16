# ReminderList

Up to three reminders: an icon, one line, and a relative time.

Use at the end of Member Home. Each row is a link, 64px tall, with a chevron. You provide the icon, the line and the time.

- Include only what the screen does not already show: a plan the trainer changed, a measurement that is due, something new that is ready. Do not repeat the workout, the session or the progress figures.
- One line each, starting with the person or the action: "Arjun updated your workout plan".

## Markup (from the design system preview)

```html
<div class="rl-root demo"><ul class="rl-card rl-remind"><li><a class="rl-remind__row" href="#"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-remind__text"><span class="rl-row__body">Arjun updated your workout plan</span><span class="rl-row__meta">1 h ago</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li><li><a class="rl-remind__row" href="#"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-remind__text"><span class="rl-row__body">Record your weekly measurements</span><span class="rl-row__meta">2 h ago</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li><li><a class="rl-remind__row" href="#"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-remind__text"><span class="rl-row__body">Your diet plan for next week is ready</span><span class="rl-row__meta">Yesterday</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li></ul></div>
```
