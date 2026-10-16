# AttentionList

The Needs attention card: up to three rows, each a count, a label, a detail line and a chevron.

Use once on Admin Home. You provide the count, the label, the detail (for payments, the amount due) and the link. The card is `attention-soft` with counts in `attention`: a calm prompt, never red.

- Each row is one link, 64px tall. Hide a row whose count is zero; hide the card when all are zero.
- With four rows, add `rl-attn--dots` and put an `rl-attn__dot` after each count: filled `attention` for today, `rl-attn__dot--ring` for this week, `rl-attn__dot--ink` for payments, `rl-attn__dot--muted` for frozen. The dot supports the label; it never replaces it.
- Counts must match the same figures elsewhere on the screen.
- People instead of counts: on Trainer Home each row is one member, with their photo in place of the count, their name, and the reason in a few words ("Missed 2 sessions this week"). Four rows at most, with a "View all" link in the section head.

```html
<ul class="rl-attn">
  <li><a class="rl-attn__row" href="…">
    <span class="rl-attn__count">14</span>
    <span class="rl-attn__text"><span class="rl-row__title">Pending payments</span><span class="rl-row__meta">₹62,300 due</span></span>
    <!-- 20px chevron, class rl-attn__chev -->
  </a></li>
</ul>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><ul class="rl-attn"><li><a class="rl-attn__row" href="#"><span class="rl-attn__count">23</span><span class="rl-attn__text"><span class="rl-row__title">Memberships expiring soon</span><span class="rl-row__meta">In the next 7 days</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li><li><a class="rl-attn__row" href="#"><span class="rl-attn__count">14</span><span class="rl-attn__text"><span class="rl-row__title">Pending payments</span><span class="rl-row__meta">₹62,300 due</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li><li><a class="rl-attn__row" href="#"><span class="rl-attn__count">9</span><span class="rl-attn__text"><span class="rl-row__title">Follow-ups due today</span><span class="rl-row__meta">Calls and messages to make</span></span><Icon class="rl-icon rl-icon--sm rl-attn__chev"/></a></li></ul></div>
```
